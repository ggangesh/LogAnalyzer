"""
Database API Router for LogSage AI
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..services.database_service import db_service
from ..models.database import LogEntry, FileMetadata

router = APIRouter(prefix="/api/v1/database", tags=["database"])


@router.post("/initialize")
async def initialize_database():
    """Initialize database tables"""
    try:
        await db_service.initialize_database()
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


@router.get("/files/{file_id}/metadata")
async def get_file_metadata(file_id: str):
    """Get file metadata"""
    try:
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File metadata not found")
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metadata: {str(e)}")


@router.get("/files/{file_id}/logs")
async def get_log_entries(
    file_id: str, 
    limit: int = 1000, 
    offset: int = 0
):
    """Get log entries for a file"""
    try:
        entries = await db_service.get_log_entries(file_id, limit, offset)
        return {
            "file_id": file_id,
            "entries": entries,
            "limit": limit,
            "offset": offset,
            "count": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving log entries: {str(e)}")


@router.get("/files/{file_id}/logs/time-range")
async def get_log_entries_by_time_range(
    file_id: str, 
    start_time: datetime, 
    end_time: datetime
):
    """Get log entries within time range"""
    try:
        entries = await db_service.get_log_entries_by_time_range(file_id, start_time, end_time)
        return {
            "file_id": file_id,
            "start_time": start_time,
            "end_time": end_time,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving log entries: {str(e)}")


@router.get("/files/{file_id}/statistics")
async def get_log_statistics(file_id: str):
    """Get comprehensive log statistics"""
    try:
        stats = await db_service.get_log_statistics(file_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.put("/files/{file_id}/metadata")
async def update_file_metadata(file_id: str, updates: Dict[str, Any]):
    """Update file metadata"""
    try:
        success = await db_service.update_file_metadata(file_id, **updates)
        if not success:
            raise HTTPException(status_code=404, detail="File not found or no updates provided")
        return {"message": "Metadata updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating metadata: {str(e)}")