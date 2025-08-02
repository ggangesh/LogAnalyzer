from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json

from ..services.log_parser import LogParser, LogFormat
from ..services.time_filter import TimeFilterService, TimeRange
from ..services.file_service import FileService

router = APIRouter(prefix="/api/v1/logs", tags=["Log Analysis"])

# Initialize services
log_parser = LogParser()
time_filter_service = TimeFilterService()
file_service = FileService()

@router.get("/parse/{file_id}")
async def parse_log_file(
    file_id: str,
    include_raw: bool = Query(False, description="Include raw log lines in response"),
    max_entries: int = Query(1000, description="Maximum number of entries to return")
):
    """Parse a log file and return structured data"""
    try:
        # Get file path from file service
        file_path = file_service.get_file_path(file_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse the log file
        parse_result = log_parser.parse_file(file_path)
        
        # Limit entries if requested
        if max_entries and len(parse_result.entries) > max_entries:
            parse_result.entries = parse_result.entries[:max_entries]
        
        # Prepare response
        response = {
            "file_id": file_id,
            "format_detected": parse_result.format_detected.value,
            "total_lines": parse_result.total_lines,
            "parsed_lines": parse_result.parsed_lines,
            "error_count": len(parse_result.errors),
            "errors": parse_result.errors[:10] if parse_result.errors else [],  # Limit errors in response
            "entries": []
        }
        
        # Add entries to response
        for entry in parse_result.entries:
            entry_data = {
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "level": entry.level,
                "message": entry.message,
                "source": entry.source,
                "line_number": entry.line_number,
                "parsed_data": entry.parsed_data
            }
            
            if include_raw:
                entry_data["raw_line"] = entry.raw_line
            
            response["entries"].append(entry_data)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")

@router.get("/parse/{file_id}/format")
async def detect_log_format(file_id: str):
    """Detect the format of a log file"""
    try:
        file_path = file_service.get_file_path(file_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        format_detected = log_parser.detect_format(file_path)
        
        return {
            "file_id": file_id,
            "format": format_detected.value,
            "description": f"Detected format: {format_detected.value}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting format: {str(e)}")

@router.get("/filters/quick")
async def get_quick_filters():
    """Get available quick time filters"""
    try:
        filters = time_filter_service.get_quick_filters()
        return {
            "filters": filters,
            "count": len(filters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filters: {str(e)}")

@router.post("/filter/{file_id}")
async def filter_logs_by_time(
    file_id: str,
    filter_type: str = Query(..., description="Filter type (e.g., 'last_1h', 'last_24h', 'custom')"),
    start_time: Optional[str] = Query(None, description="Start time for custom filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time for custom filter (ISO format)"),
    include_insights: bool = Query(False, description="Include time-based insights"),
    max_entries: int = Query(1000, description="Maximum number of entries to return")
):
    """Filter log entries by time range"""
    try:
        # Get file path
        file_path = file_service.get_file_path(file_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse the log file first
        parse_result = log_parser.parse_file(file_path)
        
        # Create time range
        if filter_type == "custom":
            if not start_time or not end_time:
                raise HTTPException(status_code=400, detail="Start time and end time required for custom filter")
            time_range = time_filter_service.create_custom_range(start_time, end_time)
        else:
            time_range = filter_type
        
        # Filter entries
        filter_result = time_filter_service.filter_entries(parse_result.entries, time_range)
        
        # Limit entries if requested
        if max_entries and len(filter_result.filtered_entries) > max_entries:
            filter_result.filtered_entries = filter_result.filtered_entries[:max_entries]
        
        # Prepare response
        response = {
            "file_id": file_id,
            "filter_type": filter_type,
            "time_range": {
                "start_time": filter_result.time_range.start_time.isoformat() if filter_result.time_range.start_time else None,
                "end_time": filter_result.time_range.end_time.isoformat() if filter_result.time_range.end_time else None,
                "description": filter_result.time_range.description
            },
            "statistics": filter_result.statistics,
            "total_entries": filter_result.total_entries,
            "filtered_count": filter_result.filtered_count,
            "entries": []
        }
        
        # Add filtered entries
        for entry in filter_result.filtered_entries:
            entry_data = {
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "level": entry.level,
                "message": entry.message,
                "source": entry.source,
                "line_number": entry.line_number,
                "parsed_data": entry.parsed_data
            }
            response["entries"].append(entry_data)
        
        # Add insights if requested
        if include_insights:
            insights = time_filter_service.get_time_based_insights(parse_result.entries, time_range)
            response["insights"] = insights
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering logs: {str(e)}")

@router.get("/insights/{file_id}")
async def get_log_insights(
    file_id: str,
    filter_type: str = Query("last_24h", description="Time filter to apply"),
    start_time: Optional[str] = Query(None, description="Start time for custom filter"),
    end_time: Optional[str] = Query(None, description="End time for custom filter")
):
    """Get insights and analysis for log entries"""
    try:
        # Get file path
        file_path = file_service.get_file_path(file_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse the log file
        parse_result = log_parser.parse_file(file_path)
        
        # Create time range
        if filter_type == "custom":
            if not start_time or not end_time:
                raise HTTPException(status_code=400, detail="Start time and end time required for custom filter")
            time_range = time_filter_service.create_custom_range(start_time, end_time)
        else:
            time_range = filter_type
        
        # Get insights
        insights = time_filter_service.get_time_based_insights(parse_result.entries, time_range)
        
        return {
            "file_id": file_id,
            "filter_type": filter_type,
            "time_range": {
                "start_time": time_range.start_time.isoformat() if time_range.start_time else None,
                "end_time": time_range.end_time.isoformat() if time_range.end_time else None,
                "description": time_range.description
            },
            "insights": insights
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting insights: {str(e)}")

@router.get("/statistics/{file_id}")
async def get_log_statistics(
    file_id: str,
    filter_type: Optional[str] = Query(None, description="Optional time filter to apply")
):
    """Get comprehensive statistics for log entries"""
    try:
        # Get file path
        file_path = file_service.get_file_path(file_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse the log file
        parse_result = log_parser.parse_file(file_path)
        
        # Prepare base statistics
        statistics = {
            "file_id": file_id,
            "format_detected": parse_result.format_detected.value,
            "total_lines": parse_result.total_lines,
            "parsed_lines": parse_result.parsed_lines,
            "error_count": len(parse_result.errors),
            "parse_success_rate": round((parse_result.parsed_lines / parse_result.total_lines) * 100, 2) if parse_result.total_lines > 0 else 0
        }
        
        # Add time-filtered statistics if filter is provided
        if filter_type:
            try:
                time_range = filter_type
                filter_result = time_filter_service.filter_entries(parse_result.entries, time_range)
                statistics["filtered"] = {
                    "filter_type": filter_type,
                    "total_entries": filter_result.total_entries,
                    "filtered_count": filter_result.filtered_count,
                    "statistics": filter_result.statistics
                }
            except Exception as e:
                statistics["filter_error"] = str(e)
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get information about supported log formats"""
    return {
        "supported_formats": [
            {
                "format": "json",
                "description": "JSON structured logs",
                "extensions": [".json"],
                "features": ["Structured data", "Nested fields", "Easy parsing"]
            },
            {
                "format": "csv",
                "description": "Comma-separated values",
                "extensions": [".csv"],
                "features": ["Tabular data", "Simple structure", "Excel compatible"]
            },
            {
                "format": "xml",
                "description": "XML structured logs",
                "extensions": [".xml"],
                "features": ["Hierarchical structure", "Rich metadata", "Schema support"]
            },
            {
                "format": "yaml",
                "description": "YAML configuration logs",
                "extensions": [".yaml", ".yml"],
                "features": ["Human readable", "Configuration files", "Structured data"]
            },
            {
                "format": "structured",
                "description": "Common log formats (Apache, Nginx, Syslog)",
                "extensions": [".log", ".txt"],
                "features": ["Standard formats", "Web server logs", "System logs"]
            },
            {
                "format": "plain",
                "description": "Plain text logs",
                "extensions": [".log", ".txt"],
                "features": ["Simple text", "Any format", "Universal compatibility"]
            }
        ],
        "timestamp_patterns": [
            "ISO format (2023-12-01T10:30:00Z)",
            "Standard format (2023-12-01 10:30:00)",
            "US format (12/01/2023 10:30:00)",
            "European format (01-12-2023 10:30:00)",
            "Unix format (Dec 01 10:30:00)"
        ],
        "log_levels": ["ERROR", "WARN", "WARNING", "INFO", "DEBUG", "CRITICAL", "FATAL"]
    } 