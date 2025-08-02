"""
SQLite Database Models for LogSage AI
"""
from datetime import datetime
from typing import Optional, List
import sqlite3
from pydantic import BaseModel
from enum import Enum


class LogLevel(str, Enum):
    """Log levels enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class LogEntry(BaseModel):
    """Log entry database model"""
    id: Optional[int] = None
    file_id: str
    timestamp: datetime
    level: LogLevel
    message: str
    source: Optional[str] = None
    raw_line: str
    line_number: int
    parsed_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class FileMetadata(BaseModel):
    """File metadata database model"""
    id: Optional[int] = None
    file_id: str
    filename: str
    file_path: str
    file_size: int
    format_type: str
    upload_time: datetime
    processing_status: str  # 'pending', 'processing', 'completed', 'failed'
    total_lines: Optional[int] = None
    parsed_lines: Optional[int] = None
    error_lines: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnomalyDetection(BaseModel):
    """Anomaly detection results model"""
    id: Optional[int] = None
    file_id: str
    anomaly_type: str  # 'volume_spike', 'error_spike', 'unusual_pattern'
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high'
    description: str
    context: Optional[dict] = None
    confidence_score: float
    created_at: Optional[datetime] = None


class VectorEmbedding(BaseModel):
    """Vector embedding storage model"""
    id: Optional[int] = None
    file_id: str
    chunk_id: str
    content: str
    embedding_vector: bytes  # Serialized vector data
    embedding_model: str
    chunk_index: int
    timestamp: datetime
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None