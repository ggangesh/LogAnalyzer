"""
Anomaly Detection Service for LogSage AI
Simple statistical analysis for MVP demo
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import re

from ..models.database import LogEntry, AnomalyDetection, LogLevel
from .database_service import db_service


class AnomalyDetectionService:
    """Service for detecting anomalies in log data using statistical methods"""
    
    def __init__(self):
        self.volume_threshold = 2.0  # Standard deviations for volume spikes
        self.error_threshold = 1.5   # Standard deviations for error rate spikes
        self.pattern_threshold = 0.05  # Minimum frequency for pattern analysis
        
    async def detect_anomalies(self, file_id: str, log_entries: List[LogEntry]) -> List[AnomalyDetection]:
        """Main method to detect all types of anomalies"""
        if not log_entries:
            return []
        
        # Convert to DataFrame for easier analysis
        df = self._logs_to_dataframe(log_entries)
        
        anomalies = []
        
        # 1. Volume-based anomalies
        volume_anomalies = await self._detect_volume_anomalies(file_id, df)
        anomalies.extend(volume_anomalies)
        
        # 2. Error rate anomalies
        error_anomalies = await self._detect_error_rate_anomalies(file_id, df)
        anomalies.extend(error_anomalies)
        
        # 3. Pattern-based anomalies
        pattern_anomalies = await self._detect_pattern_anomalies(file_id, df)
        anomalies.extend(pattern_anomalies)
        
        # 4. Time-based anomalies
        time_anomalies = await self._detect_time_anomalies(file_id, df)
        anomalies.extend(time_anomalies)
        
        # Store anomalies in database
        for anomaly in anomalies:
            await db_service.create_anomaly_detection(anomaly)
        
        return anomalies
    
    def _logs_to_dataframe(self, log_entries: List[LogEntry]) -> pd.DataFrame:
        """Convert log entries to pandas DataFrame"""
        data = []
        for entry in log_entries:
            # Handle LogLevel - it could be enum or string
            level_value = entry.level.value if hasattr(entry.level, 'value') else entry.level
            data.append({
                'timestamp': entry.timestamp,
                'level': level_value,
                'message': entry.message,
                'source': entry.source,
                'line_number': entry.line_number,
                'message_length': len(entry.message),
                'is_error': level_value in ['ERROR', 'CRITICAL'],
                'is_warning': level_value == 'WARNING'
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    
    async def _detect_volume_anomalies(self, file_id: str, df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect volume spikes using statistical analysis"""
        anomalies = []
        
        # Group by time intervals (1-hour windows)
        df_hourly = df.set_index('timestamp').resample('1H').size()
        
        if len(df_hourly) < 3:  # Need at least 3 data points
            return anomalies
        
        # Calculate statistics
        mean_volume = df_hourly.mean()
        std_volume = df_hourly.std()
        
        if std_volume == 0:  # No variation
            return anomalies
        
        # Find spikes
        threshold = mean_volume + (self.volume_threshold * std_volume)
        spikes = df_hourly[df_hourly > threshold]
        
        for timestamp, volume in spikes.items():
            severity = self._calculate_severity(volume, mean_volume, std_volume)
            confidence = min(0.95, (volume - mean_volume) / (3 * std_volume))
            
            anomaly = AnomalyDetection(
                file_id=file_id,
                anomaly_type="volume_spike",
                timestamp=timestamp,
                severity=severity,
                description=f"Volume spike detected: {int(volume)} logs/hour (normal: {int(mean_volume)})",
                context={
                    "volume": int(volume),
                    "normal_volume": int(mean_volume),
                    "threshold": int(threshold),
                    "z_score": float((volume - mean_volume) / std_volume)
                },
                confidence_score=confidence
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_error_rate_anomalies(self, file_id: str, df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect error rate spikes"""
        anomalies = []
        
        # Group by time intervals and calculate error rates
        df_hourly = df.set_index('timestamp').resample('1H').agg({
            'is_error': ['sum', 'count']
        })
        df_hourly.columns = ['error_count', 'total_count']
        df_hourly['error_rate'] = df_hourly['error_count'] / df_hourly['total_count']
        df_hourly = df_hourly.fillna(0)
        
        if len(df_hourly) < 3:
            return anomalies
        
        # Calculate statistics for error rates
        mean_error_rate = df_hourly['error_rate'].mean()
        std_error_rate = df_hourly['error_rate'].std()
        
        if std_error_rate == 0:
            return anomalies
        
        # Find error rate spikes
        threshold = mean_error_rate + (self.error_threshold * std_error_rate)
        spikes = df_hourly[df_hourly['error_rate'] > threshold]
        
        for timestamp, row in spikes.iterrows():
            if row['total_count'] > 0:  # Only consider periods with actual logs
                severity = self._calculate_severity(row['error_rate'], mean_error_rate, std_error_rate)
                confidence = min(0.95, (row['error_rate'] - mean_error_rate) / (3 * std_error_rate))
                
                anomaly = AnomalyDetection(
                    file_id=file_id,
                    anomaly_type="error_spike",
                    timestamp=timestamp,
                    severity=severity,
                    description=f"Error rate spike: {row['error_rate']:.2%} (normal: {mean_error_rate:.2%})",
                    context={
                        "error_rate": float(row['error_rate']),
                        "normal_error_rate": float(mean_error_rate),
                        "error_count": int(row['error_count']),
                        "total_count": int(row['total_count']),
                        "z_score": float((row['error_rate'] - mean_error_rate) / std_error_rate)
                    },
                    confidence_score=confidence
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_pattern_anomalies(self, file_id: str, df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect unusual patterns in log messages"""
        anomalies = []
        
        # Analyze message patterns
        message_patterns = self._extract_message_patterns(df['message'].tolist())
        
        # Calculate pattern frequencies
        total_messages = len(df)
        unusual_patterns = []
        
        for pattern, count in message_patterns.items():
            frequency = count / total_messages
            
            # Look for patterns that appear suddenly in high frequency
            if frequency > 0.1 and count > 10:  # More than 10% and at least 10 occurrences
                # Check if this pattern is concentrated in a short time period
                pattern_mask = df['message'].str.contains(re.escape(pattern[:50]), na=False)
                pattern_times = df[pattern_mask]['timestamp']
                
                if len(pattern_times) > 1:
                    time_span = (pattern_times.max() - pattern_times.min()).total_seconds()
                    if time_span < 3600:  # Pattern appears within 1 hour
                        unusual_patterns.append({
                            'pattern': pattern,
                            'count': count,
                            'frequency': frequency,
                            'time_span': time_span,
                            'first_occurrence': pattern_times.min(),
                            'last_occurrence': pattern_times.max()
                        })
        
        # Create anomalies for unusual patterns
        for pattern_info in unusual_patterns:
            severity = "high" if pattern_info['frequency'] > 0.3 else "medium"
            confidence = min(0.9, pattern_info['frequency'])
            
            anomaly = AnomalyDetection(
                file_id=file_id,
                anomaly_type="unusual_pattern",
                timestamp=pattern_info['first_occurrence'],
                severity=severity,
                description=f"Unusual pattern detected: '{pattern_info['pattern'][:100]}...' appeared {pattern_info['count']} times",
                context={
                    "pattern": pattern_info['pattern'][:200],
                    "count": pattern_info['count'],
                    "frequency": pattern_info['frequency'],
                    "time_span_seconds": pattern_info['time_span'],
                    "first_occurrence": pattern_info['first_occurrence'].isoformat(),
                    "last_occurrence": pattern_info['last_occurrence'].isoformat()
                },
                confidence_score=confidence
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_time_anomalies(self, file_id: str, df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect time-based anomalies (gaps, bursts)"""
        anomalies = []
        
        # Calculate time differences between consecutive log entries
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff().dt.total_seconds()
        
        if len(time_diffs) < 10:  # Need sufficient data
            return anomalies
        
        # Remove NaN (first entry)
        time_diffs = time_diffs.dropna()
        
        # Calculate statistics
        median_diff = time_diffs.median()
        q75 = time_diffs.quantile(0.75)
        q25 = time_diffs.quantile(0.25)
        iqr = q75 - q25
        
        # Detect large gaps (outliers using IQR method)
        gap_threshold = q75 + (1.5 * iqr)
        large_gaps = time_diffs[time_diffs > gap_threshold]
        
        for idx, gap in large_gaps.items():
            timestamp = df_sorted.iloc[idx]['timestamp']
            severity = "high" if gap > gap_threshold * 2 else "medium"
            confidence = min(0.9, gap / (gap_threshold * 3))
            
            anomaly = AnomalyDetection(
                file_id=file_id,
                anomaly_type="time_gap",
                timestamp=timestamp,
                severity=severity,
                description=f"Large time gap detected: {gap:.0f} seconds (normal: {median_diff:.0f}s)",
                context={
                    "gap_seconds": float(gap),
                    "normal_gap_seconds": float(median_diff),
                    "threshold_seconds": float(gap_threshold),
                    "gap_ratio": float(gap / median_diff) if median_diff > 0 else 0
                },
                confidence_score=confidence
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _extract_message_patterns(self, messages: List[str]) -> Dict[str, int]:
        """Extract common patterns from log messages"""
        patterns = defaultdict(int)
        
        for message in messages:
            # Extract potential patterns by removing variable parts
            # Replace numbers with placeholder
            pattern = re.sub(r'\b\d+\b', 'NUM', message)
            # Replace hexadecimal
            pattern = re.sub(r'\b[0-9a-fA-F]{8,}\b', 'HEX', pattern)
            # Replace IP addresses
            pattern = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', pattern)
            # Replace timestamps
            pattern = re.sub(r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', pattern)
            # Replace UUIDs
            pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', pattern)
            
            patterns[pattern.strip()] += 1
        
        # Filter out very rare patterns
        min_count = max(2, len(messages) * 0.01)  # At least 1% or 2 occurrences
        return {pattern: count for pattern, count in patterns.items() if count >= min_count}
    
    def _calculate_severity(self, value: float, mean: float, std: float) -> str:
        """Calculate severity based on standard deviations from mean"""
        if std == 0:
            return "low"
        
        z_score = abs(value - mean) / std
        
        if z_score > 3:
            return "high"
        elif z_score > 2:
            return "medium"
        else:
            return "low"
    
    async def get_anomaly_summary(self, file_id: str) -> Dict[str, Any]:
        """Get summary of all anomalies for a file"""
        anomalies = await db_service.get_anomalies(file_id)
        
        if not anomalies:
            return {
                "total_anomalies": 0,
                "by_type": {},
                "by_severity": {},
                "timeline": []
            }
        
        # Group by type and severity
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for anomaly in anomalies:
            by_type[anomaly.anomaly_type] += 1
            by_severity[anomaly.severity] += 1
        
        # Create timeline
        timeline = []
        for anomaly in sorted(anomalies, key=lambda x: x.timestamp):
            timeline.append({
                "timestamp": anomaly.timestamp.isoformat(),
                "type": anomaly.anomaly_type,
                "severity": anomaly.severity,
                "description": anomaly.description,
                "confidence": anomaly.confidence_score
            })
        
        return {
            "total_anomalies": len(anomalies),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "timeline": timeline
        }


# Global anomaly detection service instance
anomaly_service = AnomalyDetectionService()