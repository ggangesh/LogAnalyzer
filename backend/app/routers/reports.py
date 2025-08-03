"""
Reports Router for LogSage AI
Provides endpoints for generating and downloading JSON reports
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from ..services.reports_service import ReportsService

# Create router
router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

# Initialize service
reports_service = ReportsService()

# Pydantic models for request validation
class FilterOptions(BaseModel):
    time_range: Optional[Dict[str, Any]] = None
    log_levels: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    search_text: Optional[str] = None

@router.post("/basic/{file_id}")
async def generate_basic_report(file_id: str) -> Dict[str, Any]:
    """Generate a basic JSON report for the specified log file"""
    try:
        report = await reports_service.generate_basic_report(file_id, "basic")
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        return {
            "status": "success",
            "data": report,
            "message": "Basic report generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate basic report: {str(e)}")

@router.post("/detailed/{file_id}")
async def generate_detailed_report(
    file_id: str,
    include_anomalies: bool = Query(True, description="Include anomaly analysis in report"),
    include_summary: bool = Query(True, description="Include AI summary in report")
) -> Dict[str, Any]:
    """Generate a detailed JSON report with comprehensive log analysis"""
    try:
        report = await reports_service.generate_detailed_report(
            file_id, include_anomalies, include_summary
        )
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        return {
            "status": "success", 
            "data": report,
            "message": "Detailed report generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate detailed report: {str(e)}")

@router.post("/filtered/{file_id}")
async def generate_filtered_report(
    file_id: str,
    filter_options: FilterOptions = Body(..., description="Filter criteria for the report")
) -> Dict[str, Any]:
    """Generate a filtered JSON report based on specified criteria"""
    try:
        report = await reports_service.generate_filtered_report(
            file_id, filter_options.dict(exclude_none=True)
        )
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        return {
            "status": "success",
            "data": report,
            "message": "Filtered report generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate filtered report: {str(e)}")

@router.get("/download/basic/{file_id}")
async def download_basic_report(file_id: str):
    """Download basic report as JSON file"""
    try:
        report = await reports_service.generate_basic_report(file_id, "basic")
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        # Create filename with timestamp
        filename = f"logsage_basic_report_{file_id}_{int(datetime.now().timestamp())}.json"
        
        return JSONResponse(
            content=report,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download basic report: {str(e)}")

@router.get("/download/detailed/{file_id}")
async def download_detailed_report(
    file_id: str,
    include_anomalies: bool = Query(True, description="Include anomaly analysis"),
    include_summary: bool = Query(True, description="Include AI summary")
):
    """Download detailed report as JSON file"""
    try:
        report = await reports_service.generate_detailed_report(
            file_id, include_anomalies, include_summary
        )
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        # Create filename with timestamp
        filename = f"logsage_detailed_report_{file_id}_{int(datetime.now().timestamp())}.json"
        
        return JSONResponse(
            content=report,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download detailed report: {str(e)}")

@router.post("/download/filtered/{file_id}")
async def download_filtered_report(
    file_id: str,
    filter_options: FilterOptions = Body(..., description="Filter criteria for the report")
):
    """Download filtered report as JSON file"""
    try:
        report = await reports_service.generate_filtered_report(
            file_id, filter_options.dict(exclude_none=True)
        )
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to generate report"))
        
        # Create filename with timestamp and filter info
        filter_suffix = "_".join([
            f"levels-{'-'.join(filter_options.log_levels)}" if filter_options.log_levels else "",
            f"time-{filter_options.time_range.get('quick_filter', 'custom')}" if filter_options.time_range else "",
            f"search-{filter_options.search_text.replace(' ', '-')}" if filter_options.search_text else ""
        ]).strip("_") or "custom"
        
        filename = f"logsage_filtered_report_{file_id}_{filter_suffix}_{int(datetime.now().timestamp())}.json"
        
        return JSONResponse(
            content=report,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download filtered report: {str(e)}")

@router.get("/types")
async def get_report_types() -> Dict[str, Any]:
    """Get information about available report types and options"""
    try:
        types_info = await reports_service.get_available_report_types()
        
        return {
            "status": "success",
            "data": types_info,
            "message": "Report types information retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report types: {str(e)}")

@router.get("/preview/{file_id}")
async def preview_report_data(
    file_id: str,
    report_type: str = Query("basic", description="Type of report to preview (basic, detailed, filtered)"),
    limit: int = Query(10, ge=1, le=100, description="Number of sample records to include")
) -> Dict[str, Any]:
    """Preview report data without generating full report"""
    try:
        if report_type == "basic":
            report = await reports_service.generate_basic_report(file_id)
        elif report_type == "detailed":
            # Generate detailed report but limit logs data for preview
            report = await reports_service.generate_detailed_report(file_id, True, False)
            if "logs_data" in report:
                report["logs_data"] = report["logs_data"][:limit]
        else:
            # Default to basic for unknown types
            report = await reports_service.generate_basic_report(file_id)
        
        if report.get("status") == "error":
            raise HTTPException(status_code=500, detail=report.get("message", "Failed to preview report"))
        
        # Create preview summary
        preview = {
            "report_metadata": report.get("report_metadata", {}),
            "file_summary": report.get("file_summary", {}),
            "sample_data": {
                "logs": report.get("sample_logs", [])[:limit] or report.get("logs_data", [])[:limit],
                "anomalies": report.get("anomalies", {}).get("details", [])[:5] if report.get("anomalies") else [],
                "statistics": report.get("detailed_statistics", report.get("file_summary", {}))
            },
            "preview_info": {
                "report_type": report_type,
                "limited_to": limit,
                "full_report_available": True,
                "preview_generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "status": "success",
            "data": preview,
            "message": f"Report preview generated for {report_type} report"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview report: {str(e)}")

@router.get("/health")
async def reports_health() -> Dict[str, Any]:
    """Health check for reports service"""
    return {
        "status": "healthy",
        "service": "reports",
        "features": [
            "basic_reports",
            "detailed_reports",
            "filtered_reports",
            "json_export",
            "download_functionality"
        ],
        "supported_formats": ["JSON"],
        "timestamp": datetime.now().isoformat()
    }