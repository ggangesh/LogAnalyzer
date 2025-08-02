from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import mimetypes

class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    upload_time: Optional[datetime] = None

class FileValidation:
    """File validation configuration"""
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB in bytes
    ALLOWED_EXTENSIONS: List[str] = [
        '.log', '.txt', '.json', '.csv', '.xml', '.yaml', '.yml'
    ]
    ALLOWED_MIME_TYPES: List[str] = [
        'text/plain',
        'text/csv',
        'application/json',
        'application/xml',
        'text/xml',
        'application/x-yaml',
        'text/yaml'
    ]

    @classmethod
    def is_valid_extension(cls, filename: str) -> bool:
        """Check if file extension is allowed"""
        return any(filename.lower().endswith(ext) for ext in cls.ALLOWED_EXTENSIONS)
    
    @classmethod
    def is_valid_size(cls, file_size: int) -> bool:
        """Check if file size is within limits"""
        return file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def get_mime_type(cls, filename: str) -> Optional[str]:
        """Get MIME type for filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type

class UploadedFileInfo(BaseModel):
    """Information about uploaded file"""
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    processed: bool = False
    
    class Config:
        from_attributes = True