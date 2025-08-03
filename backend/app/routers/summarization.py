"""
Summarization Router for LogSage AI
Provides endpoints for generating log summaries and insights
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime

from ..services.summarization_service import SummarizationService

# Create router
router = APIRouter(prefix="/api/v1/summarization", tags=["Summarization"])

# Initialize service
summarization_service = SummarizationService()

@router.post("/daily/{file_id}")
async def generate_daily_summary(
    file_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)")
) -> Dict[str, Any]:
    """Generate a daily summary for the specified log file and date"""
    try:
        # Validate date format if provided
        if date:
            try:
                datetime.fromisoformat(date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        summary = await summarization_service.generate_daily_summary(file_id, date)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return {
            "status": "success",
            "data": summary,
            "message": f"Daily summary generated for {summary.get('date', 'unknown date')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily summary: {str(e)}")

@router.post("/weekly/{file_id}")
async def generate_weekly_summary(
    file_id: str,
    week_start: Optional[str] = Query(None, description="Week start date in YYYY-MM-DD format (defaults to current week)")
) -> Dict[str, Any]:
    """Generate a weekly summary for the specified log file"""
    try:
        # Validate date format if provided
        if week_start:
            try:
                datetime.fromisoformat(week_start)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        summary = await summarization_service.generate_weekly_summary(file_id, week_start)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return {
            "status": "success",
            "data": summary,
            "message": f"Weekly summary generated for week starting {summary.get('week_start', 'unknown date')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly summary: {str(e)}")

@router.get("/statistics/{file_id}")
async def get_summary_statistics(file_id: str) -> Dict[str, Any]:
    """Get overall summary statistics for a log file"""
    try:
        stats = await summarization_service.get_summary_statistics(file_id)
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "status": "success",
            "data": stats,
            "message": "Summary statistics retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary statistics: {str(e)}")

@router.get("/insights/{file_id}")
async def get_log_insights(
    file_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze (1-30)")
) -> Dict[str, Any]:
    """Get insights for the specified number of days"""
    try:
        end_date = datetime.now()
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        insights = []
        
        if days == 1:
            # Single day insights
            daily_summary = await summarization_service.generate_daily_summary(
                file_id, start_date.isoformat()
            )
            insights = daily_summary.get("key_insights", [])
        elif days <= 7:
            # Weekly insights
            weekly_summary = await summarization_service.generate_weekly_summary(
                file_id, start_date.isoformat()
            )
            insights = [
                f"Weekly average: {weekly_summary.get('weekly_trends', {}).get('average_daily_logs', 0)} logs/day",
                f"Busiest day: {weekly_summary.get('weekly_trends', {}).get('busiest_day', 'Unknown')}",
                f"Total errors this week: {weekly_summary.get('weekly_trends', {}).get('total_errors', 0)}"
            ]
        else:
            # Multi-week insights (simplified)
            stats = await summarization_service.get_summary_statistics(file_id)
            insights = [
                f"Total logs in file: {stats.get('total_logs', 0)}",
                f"Total anomalies detected: {stats.get('total_anomalies', 0)}",
                "Extended analysis available via daily/weekly summaries"
            ]
        
        return {
            "status": "success",
            "data": {
                "file_id": file_id,
                "analysis_period": f"{days} day{'s' if days != 1 else ''}",
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            },
            "message": f"Insights generated for {days} day period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.get("/health")
async def summarization_health() -> Dict[str, Any]:
    """Health check for summarization service"""
    return {
        "status": "healthy",
        "service": "summarization",
        "features": [
            "daily_summaries",
            "weekly_summaries", 
            "ai_insights",
            "statistics",
            "trend_analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }