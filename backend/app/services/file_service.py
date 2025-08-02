import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional
from datetime import datetime

from app.models.upload import FileValidation, UploadedFileInfo

class FileService:
    """Service for handling file operations"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> UploadedFileInfo:
        """Save uploaded file to disk with validation"""
        
        # Validate file
        await self._validate_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / stored_filename
        
        # Get file size
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer for validation
        await file.seek(0)
        
        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as buffer:
                await buffer.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Create file info
        file_info = UploadedFileInfo(
            id=file_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_size=file_size,
            content_type=file.content_type or FileValidation.get_mime_type(file.filename),
            upload_timestamp=datetime.now(),
            processed=False
        )
        
        return file_info
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        
        # Check filename
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
        
        # Check file extension
        if not FileValidation.is_valid_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed extensions: {', '.join(FileValidation.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer
        
        if not FileValidation.is_valid_size(file_size):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {FileValidation.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check MIME type if available
        if file.content_type:
            if file.content_type not in FileValidation.ALLOWED_MIME_TYPES:
                # Only warn, don't reject based on MIME type alone
                pass
    
    def get_file_path(self, stored_filename: str) -> Path:
        """Get full path to stored file"""
        return self.upload_dir / stored_filename
    
    def delete_file(self, stored_filename: str) -> bool:
        """Delete stored file"""
        try:
            file_path = self.get_file_path(stored_filename)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, stored_filename: str) -> bool:
        """Check if file exists"""
        return self.get_file_path(stored_filename).exists()

# Global instance
file_service = FileService()