from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from .log_parser import LogEntry, ParseResult

class TimeFilterType(Enum):
    """Types of time filters"""
    CUSTOM = "custom"
    LAST_1H = "last_1h"
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_YEAR = "this_year"

@dataclass
class TimeRange:
    """Represents a time range for filtering"""
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    filter_type: TimeFilterType
    description: str

@dataclass
class FilterResult:
    """Result of filtering operation"""
    filtered_entries: List[LogEntry]
    total_entries: int
    filtered_count: int
    time_range: TimeRange
    statistics: Dict[str, Any]

class TimeFilterService:
    """Advanced time-based filtering system for log analysis"""
    
    def __init__(self):
        self.quick_filters = self._initialize_quick_filters()
    
    def _initialize_quick_filters(self) -> Dict[str, TimeRange]:
        """Initialize predefined time filter ranges"""
        now = datetime.now()
        
        return {
            'last_1h': TimeRange(
                start_time=now - timedelta(hours=1),
                end_time=now,
                filter_type=TimeFilterType.LAST_1H,
                description="Last 1 hour"
            ),
            'last_24h': TimeRange(
                start_time=now - timedelta(hours=24),
                end_time=now,
                filter_type=TimeFilterType.LAST_24H,
                description="Last 24 hours"
            ),
            'last_7d': TimeRange(
                start_time=now - timedelta(days=7),
                end_time=now,
                filter_type=TimeFilterType.LAST_7D,
                description="Last 7 days"
            ),
            'last_30d': TimeRange(
                start_time=now - timedelta(days=30),
                end_time=now,
                filter_type=TimeFilterType.LAST_30D,
                description="Last 30 days"
            ),
            'today': TimeRange(
                start_time=now.replace(hour=0, minute=0, second=0, microsecond=0),
                end_time=now,
                filter_type=TimeFilterType.TODAY,
                description="Today"
            ),
            'yesterday': TimeRange(
                start_time=(now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                end_time=now.replace(hour=0, minute=0, second=0, microsecond=0),
                filter_type=TimeFilterType.YESTERDAY,
                description="Yesterday"
            ),
            'this_week': TimeRange(
                start_time=(now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
                end_time=now,
                filter_type=TimeFilterType.THIS_WEEK,
                description="This week"
            ),
            'this_month': TimeRange(
                start_time=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                end_time=now,
                filter_type=TimeFilterType.THIS_MONTH,
                description="This month"
            ),
            'this_year': TimeRange(
                start_time=now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                end_time=now,
                filter_type=TimeFilterType.THIS_YEAR,
                description="This year"
            )
        }
    
    def get_quick_filters(self) -> Dict[str, Dict[str, Any]]:
        """Get available quick filters with metadata"""
        result = {}
        for key, time_range in self.quick_filters.items():
            result[key] = {
                'start_time': time_range.start_time.isoformat() if time_range.start_time else None,
                'end_time': time_range.end_time.isoformat() if time_range.end_time else None,
                'filter_type': time_range.filter_type.value,
                'description': time_range.description
            }
        return result
    
    def create_custom_range(self, start_time: Union[str, datetime], 
                          end_time: Union[str, datetime]) -> TimeRange:
        """Create a custom time range"""
        # Convert string to datetime if needed
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        return TimeRange(
            start_time=start_time,
            end_time=end_time,
            filter_type=TimeFilterType.CUSTOM,
            description=f"Custom range: {start_time} to {end_time}"
        )
    
    def filter_entries(self, entries: List[LogEntry], 
                      time_range: Union[str, TimeRange]) -> FilterResult:
        """Filter log entries by time range"""
        # Convert string filter to TimeRange if needed
        if isinstance(time_range, str):
            if time_range in self.quick_filters:
                time_range = self.quick_filters[time_range]
            else:
                raise ValueError(f"Unknown quick filter: {time_range}")
        
        filtered_entries = []
        total_entries = len(entries)
        
        for entry in entries:
            if entry.timestamp is None:
                continue
            
            # Check if entry is within time range
            if time_range.start_time and entry.timestamp < time_range.start_time:
                continue
            if time_range.end_time and entry.timestamp > time_range.end_time:
                continue
            
            filtered_entries.append(entry)
        
        # Calculate statistics
        statistics = self._calculate_statistics(filtered_entries, time_range)
        
        return FilterResult(
            filtered_entries=filtered_entries,
            total_entries=total_entries,
            filtered_count=len(filtered_entries),
            time_range=time_range,
            statistics=statistics
        )
    
    def filter_parse_result(self, parse_result: ParseResult, 
                          time_range: Union[str, TimeRange]) -> FilterResult:
        """Filter a ParseResult by time range"""
        return self.filter_entries(parse_result.entries, time_range)
    
    def filter_dataframe(self, df: pd.DataFrame, 
                        time_range: Union[str, TimeRange]) -> pd.DataFrame:
        """Filter pandas DataFrame by time range"""
        # Convert string filter to TimeRange if needed
        if isinstance(time_range, str):
            if time_range in self.quick_filters:
                time_range = self.quick_filters[time_range]
            else:
                raise ValueError(f"Unknown quick filter: {time_range}")
        
        if 'timestamp' not in df.columns:
            return df
        
        # Create mask for filtering
        mask = pd.Series([True] * len(df), index=df.index)
        
        if time_range.start_time:
            mask &= df['timestamp'] >= time_range.start_time
        
        if time_range.end_time:
            mask &= df['timestamp'] <= time_range.end_time
        
        return df[mask].copy()
    
    def _calculate_statistics(self, entries: List[LogEntry], 
                            time_range: TimeRange) -> Dict[str, Any]:
        """Calculate statistics for filtered entries"""
        if not entries:
            return {
                'total_entries': 0,
                'entries_with_timestamp': 0,
                'level_distribution': {},
                'source_distribution': {},
                'time_span': None,
                'average_entries_per_hour': 0
            }
        
        # Basic counts
        total_entries = len(entries)
        entries_with_timestamp = len([e for e in entries if e.timestamp is not None])
        
        # Level distribution
        level_distribution = {}
        for entry in entries:
            level = entry.level or 'UNKNOWN'
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # Source distribution
        source_distribution = {}
        for entry in entries:
            source = entry.source
            source_distribution[source] = source_distribution.get(source, 0) + 1
        
        # Time span calculation
        timestamps = [e.timestamp for e in entries if e.timestamp is not None]
        time_span = None
        average_entries_per_hour = 0
        
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_span = {
                'start': min_time.isoformat(),
                'end': max_time.isoformat(),
                'duration_hours': (max_time - min_time).total_seconds() / 3600
            }
            
            # Calculate average entries per hour
            if time_span['duration_hours'] > 0:
                average_entries_per_hour = total_entries / time_span['duration_hours']
        
        return {
            'total_entries': total_entries,
            'entries_with_timestamp': entries_with_timestamp,
            'level_distribution': level_distribution,
            'source_distribution': source_distribution,
            'time_span': time_span,
            'average_entries_per_hour': round(average_entries_per_hour, 2)
        }
    
    def get_time_based_insights(self, entries: List[LogEntry], 
                              time_range: Union[str, TimeRange]) -> Dict[str, Any]:
        """Get insights based on time patterns"""
        if isinstance(time_range, str):
            if time_range in self.quick_filters:
                time_range = self.quick_filters[time_range]
            else:
                raise ValueError(f"Unknown quick filter: {time_range}")
        
        filtered_result = self.filter_entries(entries, time_range)
        
        if not filtered_result.filtered_entries:
            return {
                'message': 'No entries found in the specified time range',
                'patterns': {},
                'anomalies': [],
                'trends': {}
            }
        
        # Analyze patterns
        patterns = self._analyze_patterns(filtered_result.filtered_entries)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(filtered_result.filtered_entries)
        
        # Analyze trends
        trends = self._analyze_trends(filtered_result.filtered_entries, time_range)
        
        return {
            'patterns': patterns,
            'anomalies': anomalies,
            'trends': trends,
            'statistics': filtered_result.statistics
        }
    
    def _analyze_patterns(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Analyze patterns in log entries"""
        patterns = {
            'hourly_distribution': {},
            'level_patterns': {},
            'error_patterns': []
        }
        
        # Hourly distribution
        for entry in entries:
            if entry.timestamp:
                hour = entry.timestamp.hour
                patterns['hourly_distribution'][hour] = patterns['hourly_distribution'].get(hour, 0) + 1
        
        # Level patterns
        for entry in entries:
            level = entry.level or 'UNKNOWN'
            if level not in patterns['level_patterns']:
                patterns['level_patterns'][level] = {
                    'count': 0,
                    'messages': []
                }
            patterns['level_patterns'][level]['count'] += 1
            patterns['level_patterns'][level]['messages'].append(entry.message[:100])  # First 100 chars
        
        # Error patterns (entries with ERROR level)
        error_entries = [e for e in entries if e.level and 'ERROR' in e.level.upper()]
        patterns['error_patterns'] = [
            {
                'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                'message': e.message,
                'source': e.source
            }
            for e in error_entries[:10]  # Top 10 errors
        ]
        
        return patterns
    
    def _detect_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect anomalies in log entries"""
        anomalies = []
        
        if not entries:
            return anomalies
        
        # Group entries by hour
        hourly_counts = {}
        for entry in entries:
            if entry.timestamp:
                hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        if not hourly_counts:
            return anomalies
        
        # Calculate average and standard deviation
        counts = list(hourly_counts.values())
        avg_count = sum(counts) / len(counts)
        
        # Detect spikes (more than 2x average)
        for hour, count in hourly_counts.items():
            if count > avg_count * 2:
                anomalies.append({
                    'type': 'volume_spike',
                    'timestamp': hour.isoformat(),
                    'count': count,
                    'average': round(avg_count, 2),
                    'description': f'Log volume spike: {count} entries vs average {round(avg_count, 2)}'
                })
        
        # Detect error spikes
        error_entries = [e for e in entries if e.level and 'ERROR' in e.level.upper()]
        if error_entries:
            error_hourly_counts = {}
            for entry in error_entries:
                if entry.timestamp:
                    hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
                    error_hourly_counts[hour_key] = error_hourly_counts.get(hour_key, 0) + 1
            
            if error_hourly_counts:
                error_counts = list(error_hourly_counts.values())
                avg_error_count = sum(error_counts) / len(error_counts)
                
                for hour, count in error_hourly_counts.items():
                    if count > avg_error_count * 3:  # 3x average for errors
                        anomalies.append({
                            'type': 'error_spike',
                            'timestamp': hour.isoformat(),
                            'count': count,
                            'average': round(avg_error_count, 2),
                            'description': f'Error spike: {count} errors vs average {round(avg_error_count, 2)}'
                        })
        
        return anomalies
    
    def _analyze_trends(self, entries: List[LogEntry], 
                       time_range: TimeRange) -> Dict[str, Any]:
        """Analyze trends in log entries"""
        trends = {
            'volume_trend': 'stable',
            'error_trend': 'stable',
            'peak_hours': [],
            'quiet_hours': []
        }
        
        if not entries:
            return trends
        
        # Analyze volume trend
        if time_range.start_time and time_range.end_time:
            duration_hours = (time_range.end_time - time_range.start_time).total_seconds() / 3600
            if duration_hours > 1:
                # Split into time periods and analyze trend
                hourly_counts = {}
                for entry in entries:
                    if entry.timestamp:
                        hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
                        hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
                
                if len(hourly_counts) > 1:
                    sorted_hours = sorted(hourly_counts.keys())
                    first_half = sum(hourly_counts[h] for h in sorted_hours[:len(sorted_hours)//2])
                    second_half = sum(hourly_counts[h] for h in sorted_hours[len(sorted_hours)//2:])
                    
                    if second_half > first_half * 1.2:
                        trends['volume_trend'] = 'increasing'
                    elif first_half > second_half * 1.2:
                        trends['volume_trend'] = 'decreasing'
        
        # Find peak and quiet hours
        hourly_distribution = {}
        for entry in entries:
            if entry.timestamp:
                hour = entry.timestamp.hour
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        if hourly_distribution:
            max_count = max(hourly_distribution.values())
            min_count = min(hourly_distribution.values())
            
            trends['peak_hours'] = [h for h, c in hourly_distribution.items() if c == max_count]
            trends['quiet_hours'] = [h for h, c in hourly_distribution.items() if c == min_count]
        
        return trends 