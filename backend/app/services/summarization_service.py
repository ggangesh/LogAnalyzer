"""
Summarization Service for LogSage AI
Provides daily log summaries and insights generation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

from .database_service import DatabaseService
from .log_parser import LogParserService
from .anomaly_detection import AnomalyDetectionService
from .chat_service import ChatService

class SummarizationService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.log_parser = LogParserService()
        self.anomaly_service = AnomalyDetectionService()
        self.chat_service = ChatService()
        
    async def generate_daily_summary(self, file_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Generate a daily summary for logs on specified date"""
        try:
            target_date = datetime.fromisoformat(date) if date else datetime.now()
            start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            
            # Get logs for the day
            logs = await self.db_service.get_logs_by_time_range(
                file_id, start_time.isoformat(), end_time.isoformat()
            )
            
            if not logs:
                return {
                    "date": target_date.date().isoformat(),
                    "total_logs": 0,
                    "summary": "No logs found for this date",
                    "key_insights": [],
                    "anomalies": [],
                    "recommendations": []
                }
            
            # Basic statistics
            total_logs = len(logs)
            log_levels = {}
            sources = {}
            hourly_distribution = {}
            
            for log in logs:
                # Count by log level
                level = log.get('level', 'unknown').lower()
                log_levels[level] = log_levels.get(level, 0) + 1
                
                # Count by source
                source = log.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
                
                # Hourly distribution
                if log.get('timestamp'):
                    try:
                        log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                        hour = log_time.hour
                        hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
                    except:
                        pass
            
            # Get anomalies for the day
            anomalies = await self.anomaly_service.get_anomalies_by_time_range(
                file_id, start_time.isoformat(), end_time.isoformat()
            )
            
            # Generate AI insights
            ai_summary = await self._generate_ai_summary(logs, log_levels, anomalies)
            
            # Calculate peak hours
            peak_hour = max(hourly_distribution.items(), key=lambda x: x[1]) if hourly_distribution else (0, 0)
            
            summary = {
                "date": target_date.date().isoformat(),
                "total_logs": total_logs,
                "summary": ai_summary.get("summary", "Daily log activity recorded"),
                "statistics": {
                    "log_levels": log_levels,
                    "top_sources": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]),
                    "peak_hour": f"{peak_hour[0]}:00" if peak_hour[1] > 0 else "No peak identified",
                    "peak_hour_count": peak_hour[1],
                    "hourly_distribution": hourly_distribution
                },
                "key_insights": ai_summary.get("insights", []),
                "anomalies": [
                    {
                        "type": anomaly.get("type", "Unknown"),
                        "severity": anomaly.get("severity", "low"),
                        "description": anomaly.get("description", ""),
                        "confidence": anomaly.get("confidence", 0)
                    }
                    for anomaly in anomalies[:5]  # Top 5 anomalies
                ],
                "recommendations": ai_summary.get("recommendations", []),
                "trends": {
                    "error_rate": round((log_levels.get('error', 0) / total_logs) * 100, 2) if total_logs > 0 else 0,
                    "warning_rate": round((log_levels.get('warning', 0) / total_logs) * 100, 2) if total_logs > 0 else 0,
                    "most_active_source": max(sources.items(), key=lambda x: x[1])[0] if sources else "None"
                }
            }
            
            return summary
            
        except Exception as e:
            return {
                "date": date or datetime.now().date().isoformat(),
                "error": str(e),
                "summary": "Failed to generate daily summary"
            }
    
    async def generate_weekly_summary(self, file_id: str, week_start: Optional[str] = None) -> Dict[str, Any]:
        """Generate a weekly summary for logs"""
        try:
            if week_start:
                start_date = datetime.fromisoformat(week_start)
            else:
                # Start of current week (Monday)
                today = datetime.now()
                start_date = today - timedelta(days=today.weekday())
            
            end_date = start_date + timedelta(days=7)
            
            # Generate daily summaries for each day
            daily_summaries = []
            total_logs = 0
            weekly_anomalies = []
            
            for i in range(7):
                day = start_date + timedelta(days=i)
                daily_summary = await self.generate_daily_summary(file_id, day.isoformat())
                daily_summaries.append(daily_summary)
                total_logs += daily_summary.get("total_logs", 0)
                weekly_anomalies.extend(daily_summary.get("anomalies", []))
            
            # Calculate weekly trends
            weekly_trends = self._calculate_weekly_trends(daily_summaries)
            
            summary = {
                "week_start": start_date.date().isoformat(),
                "week_end": end_date.date().isoformat(),
                "total_logs": total_logs,
                "daily_summaries": daily_summaries,
                "weekly_trends": weekly_trends,
                "top_anomalies": sorted(weekly_anomalies, key=lambda x: x.get("confidence", 0), reverse=True)[:10],
                "summary": f"Week of {start_date.strftime('%B %d, %Y')} - {total_logs} total log entries processed"
            }
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "summary": "Failed to generate weekly summary"
            }
    
    async def _generate_ai_summary(self, logs: List[Dict], log_levels: Dict, anomalies: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered insights from log data"""
        try:
            # Prepare context for AI
            context = f"""
            Daily Log Analysis:
            - Total logs: {len(logs)}
            - Log levels: {log_levels}
            - Anomalies detected: {len(anomalies)}
            
            Sample log entries:
            {json.dumps(logs[:5], indent=2) if logs else "No logs available"}
            
            Anomalies:
            {json.dumps(anomalies[:3], indent=2) if anomalies else "No anomalies detected"}
            """
            
            # Use demo mode for MVP
            if not hasattr(self.chat_service, 'client') or not self.chat_service.client:
                return self._generate_demo_summary(logs, log_levels, anomalies)
            
            # Generate AI summary (this would use actual AI in production)
            ai_response = await self.chat_service.analyze_logs(
                "summary", context, conversation_history=[]
            )
            
            return {
                "summary": ai_response.get("response", "Daily activity summary generated"),
                "insights": [
                    "Log analysis completed",
                    f"Processed {len(logs)} log entries",
                    f"Detected {len(anomalies)} anomalies"
                ],
                "recommendations": [
                    "Monitor error rates",
                    "Review anomaly patterns",
                    "Check system performance"
                ]
            }
            
        except Exception as e:
            return self._generate_demo_summary(logs, log_levels, anomalies)
    
    def _generate_demo_summary(self, logs: List[Dict], log_levels: Dict, anomalies: List[Dict]) -> Dict[str, Any]:
        """Generate demo summary without AI"""
        total_logs = len(logs)
        error_count = log_levels.get('error', 0)
        warning_count = log_levels.get('warning', 0)
        
        insights = []
        recommendations = []
        
        # Generate insights based on log analysis
        if total_logs > 1000:
            insights.append("High volume of log activity detected")
        elif total_logs < 10:
            insights.append("Low log activity - system may be quiet")
        
        if error_count > 0:
            insights.append(f"Found {error_count} error entries requiring attention")
            recommendations.append("Investigate error patterns and root causes")
        
        if warning_count > error_count * 2:
            insights.append("Warning-to-error ratio suggests potential escalating issues")
            recommendations.append("Monitor warnings to prevent escalation to errors")
        
        if len(anomalies) > 0:
            insights.append(f"Detected {len(anomalies)} anomalous patterns")
            recommendations.append("Review anomaly reports for system optimization")
        
        summary_text = f"Analyzed {total_logs} log entries with {error_count} errors and {warning_count} warnings."
        if len(anomalies) > 0:
            summary_text += f" Detected {len(anomalies)} anomalies requiring review."
        
        return {
            "summary": summary_text,
            "insights": insights or ["Normal log activity observed"],
            "recommendations": recommendations or ["Continue monitoring system performance"]
        }
    
    def _calculate_weekly_trends(self, daily_summaries: List[Dict]) -> Dict[str, Any]:
        """Calculate weekly trends from daily summaries"""
        daily_counts = [summary.get("total_logs", 0) for summary in daily_summaries]
        daily_errors = [summary.get("statistics", {}).get("log_levels", {}).get("error", 0) for summary in daily_summaries]
        
        avg_daily_logs = sum(daily_counts) / len(daily_counts) if daily_counts else 0
        avg_daily_errors = sum(daily_errors) / len(daily_errors) if daily_errors else 0
        
        # Find busiest and quietest days
        busiest_day_idx = daily_counts.index(max(daily_counts)) if daily_counts else 0
        quietest_day_idx = daily_counts.index(min(daily_counts)) if daily_counts else 0
        
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "average_daily_logs": round(avg_daily_logs, 1),
            "average_daily_errors": round(avg_daily_errors, 1),
            "busiest_day": days_of_week[busiest_day_idx],
            "busiest_day_count": daily_counts[busiest_day_idx],
            "quietest_day": days_of_week[quietest_day_idx],
            "quietest_day_count": daily_counts[quietest_day_idx],
            "daily_log_counts": daily_counts,
            "total_errors": sum(daily_errors)
        }
    
    async def get_summary_statistics(self, file_id: str) -> Dict[str, Any]:
        """Get overall summary statistics for a log file"""
        try:
            # Get basic file metadata
            metadata = await self.db_service.get_file_metadata(file_id)
            
            # Get all logs count
            logs = await self.db_service.get_logs(file_id, limit=None)
            total_logs = len(logs) if logs else 0
            
            # Get anomalies count
            anomalies = await self.anomaly_service.get_anomalies(file_id)
            total_anomalies = len(anomalies) if anomalies else 0
            
            return {
                "file_id": file_id,
                "filename": metadata.get("filename", "Unknown") if metadata else "Unknown",
                "total_logs": total_logs,
                "total_anomalies": total_anomalies,
                "summary_available": total_logs > 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "file_id": file_id,
                "error": str(e),
                "summary_available": False
            }