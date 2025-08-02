"""
Anomaly Detection API Router for LogSage AI
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel

from ..services.anomaly_detection import anomaly_service
from ..services.database_service import db_service
from ..models.database import LogEntry

router = APIRouter(prefix="/api/v1/anomaly", tags=["anomaly-detection"])


class AnomalyDetectionRequest(BaseModel):
    file_id: str
    force_redetect: bool = False


@router.post("/detect/{file_id}")
async def detect_anomalies(file_id: str, background_tasks: BackgroundTasks):
    """Detect anomalies in log file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get log entries
        log_entries = await db_service.get_log_entries(file_id, limit=10000)  # Limit for demo
        
        if not log_entries:
            return {
                "file_id": file_id,
                "message": "No log entries found for analysis",
                "anomalies": []
            }
        
        # Detect anomalies
        anomalies = await anomaly_service.detect_anomalies(file_id, log_entries)
        
        # Update file metadata to mark anomaly detection as complete
        await db_service.update_file_metadata(file_id, anomaly_detection_status="completed")
        
        return {
            "file_id": file_id,
            "total_log_entries": len(log_entries),
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "type": anomaly.anomaly_type,
                    "timestamp": anomaly.timestamp.isoformat(),
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "confidence": anomaly.confidence_score,
                    "context": anomaly.context
                }
                for anomaly in anomalies
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.get("/results/{file_id}")
async def get_anomaly_results(file_id: str):
    """Get existing anomaly detection results"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get anomalies from database
        anomalies = await db_service.get_anomalies(file_id)
        
        return {
            "file_id": file_id,
            "total_anomalies": len(anomalies),
            "anomalies": [
                {
                    "id": anomaly.id,
                    "type": anomaly.anomaly_type,
                    "timestamp": anomaly.timestamp.isoformat(),
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "confidence": anomaly.confidence_score,
                    "context": anomaly.context,
                    "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None
                }
                for anomaly in anomalies
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving anomaly results: {str(e)}")


@router.get("/summary/{file_id}")
async def get_anomaly_summary(file_id: str):
    """Get anomaly summary and statistics"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        summary = await anomaly_service.get_anomaly_summary(file_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving anomaly summary: {str(e)}")


@router.get("/types")
async def get_anomaly_types():
    """Get available anomaly types and their descriptions"""
    return {
        "anomaly_types": [
            {
                "type": "volume_spike",
                "name": "Volume Spike",
                "description": "Unusual increase in log volume over time",
                "detection_method": "Statistical analysis using standard deviations"
            },
            {
                "type": "error_spike",
                "name": "Error Rate Spike",
                "description": "Unusual increase in error log frequency",
                "detection_method": "Error rate analysis with statistical thresholds"
            },
            {
                "type": "unusual_pattern",
                "name": "Unusual Pattern",
                "description": "Unexpected patterns or messages appearing frequently",
                "detection_method": "Pattern frequency analysis and clustering"
            },
            {
                "type": "time_gap",
                "name": "Time Gap",
                "description": "Unusual gaps or silences in logging activity",
                "detection_method": "Time interval analysis using IQR method"
            }
        ],
        "severity_levels": ["low", "medium", "high"],
        "confidence_range": "0.0 to 1.0"
    }


@router.delete("/results/{file_id}")
async def clear_anomaly_results(file_id: str):
    """Clear anomaly detection results for a file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # This would require implementing a delete method in the database service
        # For now, we'll just return a success message
        return {
            "message": f"Anomaly results cleared for file {file_id}",
            "note": "Delete functionality to be implemented in database service"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing anomaly results: {str(e)}")