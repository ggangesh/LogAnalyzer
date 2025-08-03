"""
Reports Service for LogSage AI
Provides JSON report generation and export functionality
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

from .database_service import DatabaseService
from .anomaly_detection import AnomalyDetectionService
from .summarization_service import SummarizationService
from .time_filter import TimeFilterService

class ReportsService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.anomaly_service = AnomalyDetectionService()
        self.summarization_service = SummarizationService()
        self.time_filter = TimeFilterService()
        
    async def generate_basic_report(self, file_id: str, report_type: str = "basic") -> Dict[str, Any]:
        """Generate a basic JSON report for the specified log file"""
        try:
            # Get file metadata
            metadata = await self.db_service.get_file_metadata(file_id)
            
            # Get basic statistics
            stats = await self.db_service.get_statistics(file_id)
            
            # Get logs summary
            logs = await self.db_service.get_logs(file_id, limit=100)  # Sample for basic report
            
            report = {
                "report_metadata": {
                    "report_id": f"report_{file_id}_{int(datetime.now().timestamp())}",
                    "report_type": report_type,
                    "generated_at": datetime.now().isoformat(),
                    "file_id": file_id,
                    "filename": metadata.get("filename", "Unknown") if metadata else "Unknown"
                },
                "file_summary": {
                    "total_logs": stats.get("total_logs", 0) if stats else 0,
                    "date_range": {
                        "earliest": stats.get("earliest_timestamp") if stats else None,
                        "latest": stats.get("latest_timestamp") if stats else None
                    },
                    "log_levels": stats.get("level_distribution", {}) if stats else {},
                    "sources": stats.get("source_distribution", {}) if stats else {}
                },
                "sample_logs": [
                    {
                        "timestamp": log.get("timestamp"),
                        "level": log.get("level"),
                        "source": log.get("source"),
                        "message": log.get("message", "")[:200]  # Truncate long messages
                    }
                    for log in (logs or [])[:10]  # Top 10 samples
                ],
                "export_info": {
                    "format": "JSON",
                    "version": "1.0",
                    "total_records": len(logs) if logs else 0
                }
            }
            
            return report
            
        except Exception as e:
            return {
                "report_metadata": {
                    "report_id": f"error_report_{int(datetime.now().timestamp())}",
                    "generated_at": datetime.now().isoformat(),
                    "file_id": file_id,
                    "error": str(e)
                },
                "status": "error",
                "message": "Failed to generate basic report"
            }
    
    async def generate_detailed_report(self, file_id: str, include_anomalies: bool = True, include_summary: bool = True) -> Dict[str, Any]:
        """Generate a detailed JSON report with anomalies and summaries"""
        try:
            # Get basic report data
            basic_report = await self.generate_basic_report(file_id, "detailed")
            
            # Get all logs for detailed analysis
            all_logs = await self.db_service.get_logs(file_id, limit=None)
            
            # Add detailed statistics
            detailed_stats = await self._calculate_detailed_statistics(all_logs or [])
            
            # Update report with detailed information
            report = basic_report.copy()
            report["report_metadata"]["report_type"] = "detailed"
            report["detailed_statistics"] = detailed_stats
            
            # Add anomalies if requested
            if include_anomalies:
                anomalies = await self.anomaly_service.get_anomalies(file_id)
                report["anomalies"] = {
                    "total_count": len(anomalies) if anomalies else 0,
                    "by_severity": self._group_anomalies_by_severity(anomalies or []),
                    "details": [
                        {
                            "type": anomaly.get("type"),
                            "severity": anomaly.get("severity"),
                            "timestamp": anomaly.get("timestamp"),
                            "description": anomaly.get("description"),
                            "confidence": anomaly.get("confidence")
                        }
                        for anomaly in (anomalies or [])
                    ]
                }
            
            # Add summary if requested
            if include_summary:
                summary_stats = await self.summarization_service.get_summary_statistics(file_id)
                today_summary = await self.summarization_service.generate_daily_summary(file_id)
                
                report["summary"] = {
                    "daily_summary": today_summary,
                    "overall_stats": summary_stats,
                    "key_insights": today_summary.get("key_insights", []),
                    "recommendations": today_summary.get("recommendations", [])
                }
            
            # Add full logs data for detailed report
            report["logs_data"] = [
                {
                    "id": log.get("id"),
                    "timestamp": log.get("timestamp"),
                    "level": log.get("level"),
                    "source": log.get("source"),
                    "message": log.get("message"),
                    "raw_data": log.get("raw_data")
                }
                for log in (all_logs or [])
            ]
            
            report["export_info"]["total_records"] = len(all_logs) if all_logs else 0
            
            return report
            
        except Exception as e:
            return {
                "report_metadata": {
                    "report_id": f"error_detailed_report_{int(datetime.now().timestamp())}",
                    "generated_at": datetime.now().isoformat(),
                    "file_id": file_id,
                    "error": str(e)
                },
                "status": "error",
                "message": "Failed to generate detailed report"
            }
    
    async def generate_filtered_report(self, file_id: str, filter_options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report with filtered data based on provided criteria"""
        try:
            # Apply time filter if specified
            filtered_logs = []
            
            if filter_options.get("time_range"):
                time_range = filter_options["time_range"]
                if time_range.get("quick_filter"):
                    # Use predefined quick filter
                    filter_result = await self.time_filter.apply_quick_filter(
                        file_id, time_range["quick_filter"]
                    )
                    filtered_logs = filter_result.get("filtered_logs", [])
                elif time_range.get("start_time") and time_range.get("end_time"):
                    # Use custom time range
                    filter_result = await self.time_filter.filter_by_time_range(
                        file_id, time_range["start_time"], time_range["end_time"]
                    )
                    filtered_logs = filter_result.get("filtered_logs", [])
            else:
                # No time filter, get all logs
                filtered_logs = await self.db_service.get_logs(file_id, limit=None) or []
            
            # Apply level filter if specified
            if filter_options.get("log_levels"):
                target_levels = [level.lower() for level in filter_options["log_levels"]]
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.get("level", "").lower() in target_levels
                ]
            
            # Apply source filter if specified
            if filter_options.get("sources"):
                target_sources = filter_options["sources"]
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.get("source") in target_sources
                ]
            
            # Apply text search if specified
            if filter_options.get("search_text"):
                search_text = filter_options["search_text"].lower()
                filtered_logs = [
                    log for log in filtered_logs
                    if search_text in log.get("message", "").lower()
                ]
            
            # Generate report with filtered data
            report = {
                "report_metadata": {
                    "report_id": f"filtered_report_{file_id}_{int(datetime.now().timestamp())}",
                    "report_type": "filtered",
                    "generated_at": datetime.now().isoformat(),
                    "file_id": file_id,
                    "filters_applied": filter_options
                },
                "filter_summary": {
                    "total_filtered_logs": len(filtered_logs),
                    "filter_criteria": filter_options,
                    "reduction_percentage": self._calculate_reduction_percentage(file_id, len(filtered_logs))
                },
                "filtered_statistics": await self._calculate_detailed_statistics(filtered_logs),
                "filtered_logs": [
                    {
                        "timestamp": log.get("timestamp"),
                        "level": log.get("level"),
                        "source": log.get("source"),
                        "message": log.get("message")
                    }
                    for log in filtered_logs
                ],
                "export_info": {
                    "format": "JSON",
                    "version": "1.0",
                    "total_records": len(filtered_logs)
                }
            }
            
            return report
            
        except Exception as e:
            return {
                "report_metadata": {
                    "report_id": f"error_filtered_report_{int(datetime.now().timestamp())}",
                    "generated_at": datetime.now().isoformat(),
                    "file_id": file_id,
                    "error": str(e)
                },
                "status": "error",
                "message": "Failed to generate filtered report"
            }
    
    async def get_available_report_types(self) -> Dict[str, Any]:
        """Get information about available report types"""
        return {
            "report_types": {
                "basic": {
                    "name": "Basic Report",
                    "description": "Essential log statistics and sample entries",
                    "includes": ["metadata", "statistics", "sample_logs"],
                    "size": "Small",
                    "generation_time": "Fast"
                },
                "detailed": {
                    "name": "Detailed Report", 
                    "description": "Comprehensive report with anomalies and full log data",
                    "includes": ["metadata", "statistics", "all_logs", "anomalies", "summary"],
                    "size": "Large",
                    "generation_time": "Moderate"
                },
                "filtered": {
                    "name": "Filtered Report",
                    "description": "Report based on specific filter criteria",
                    "includes": ["metadata", "filtered_data", "filter_statistics"],
                    "size": "Variable",
                    "generation_time": "Fast"
                }
            },
            "filter_options": {
                "time_range": {
                    "quick_filters": ["last_1h", "last_24h", "last_7d", "last_30d"],
                    "custom_range": "start_time and end_time in ISO format"
                },
                "log_levels": ["debug", "info", "warning", "error", "critical"],
                "sources": "List of specific log sources",
                "search_text": "Text search within log messages"
            },
            "export_formats": ["JSON"],
            "version": "1.0"
        }
    
    async def _calculate_detailed_statistics(self, logs: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed statistics for a set of logs"""
        if not logs:
            return {"total_logs": 0, "message": "No logs to analyze"}
        
        # Basic counts
        total_logs = len(logs)
        
        # Level distribution
        level_dist = {}
        source_dist = {}
        hourly_dist = {}
        daily_dist = {}
        
        for log in logs:
            # Level distribution
            level = log.get("level", "unknown").lower()
            level_dist[level] = level_dist.get(level, 0) + 1
            
            # Source distribution
            source = log.get("source", "unknown")
            source_dist[source] = source_dist.get(source, 0) + 1
            
            # Time distributions
            if log.get("timestamp"):
                try:
                    log_time = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
                    hour = log_time.hour
                    date = log_time.date().isoformat()
                    
                    hourly_dist[hour] = hourly_dist.get(hour, 0) + 1
                    daily_dist[date] = daily_dist.get(date, 0) + 1
                except:
                    pass
        
        # Calculate rates
        error_rate = (level_dist.get("error", 0) / total_logs) * 100 if total_logs > 0 else 0
        warning_rate = (level_dist.get("warning", 0) / total_logs) * 100 if total_logs > 0 else 0
        
        return {
            "total_logs": total_logs,
            "level_distribution": level_dist,
            "source_distribution": dict(sorted(source_dist.items(), key=lambda x: x[1], reverse=True)),
            "hourly_distribution": hourly_dist,
            "daily_distribution": daily_dist,
            "rates": {
                "error_rate": round(error_rate, 2),
                "warning_rate": round(warning_rate, 2),
                "info_rate": round((level_dist.get("info", 0) / total_logs) * 100, 2) if total_logs > 0 else 0
            },
            "top_sources": dict(list(sorted(source_dist.items(), key=lambda x: x[1], reverse=True))[:5]),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _group_anomalies_by_severity(self, anomalies: List[Dict]) -> Dict[str, int]:
        """Group anomalies by severity level"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for anomaly in anomalies:
            severity = anomaly.get("severity", "low").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    async def _calculate_reduction_percentage(self, file_id: str, filtered_count: int) -> float:
        """Calculate the percentage reduction from filtering"""
        try:
            total_logs = await self.db_service.get_logs(file_id, limit=None)
            total_count = len(total_logs) if total_logs else 0
            
            if total_count == 0:
                return 0.0
            
            reduction = ((total_count - filtered_count) / total_count) * 100
            return round(reduction, 2)
        except:
            return 0.0