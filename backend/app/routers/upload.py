from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from app.models.upload import UploadResponse, UploadedFileInfo
from app.services.file_service import file_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Log file to upload"),
    description: Optional[str] = Form(None, description="Optional file description")
):
    """
    Upload a log file for analysis
    
    - **file**: Log file (supports .log, .txt, .json, .csv, .xml, .yaml formats)
    - **description**: Optional description for the file
    - **Max size**: 100MB
    """
    try:
        logger.info(f"Attempting to upload file: {file.filename}")
        
        # Save the file using file service
        file_info = await file_service.save_uploaded_file(file)
        
        logger.info(f"Successfully uploaded file: {file.filename} with ID: {file_info.id}")
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_info.id,
            filename=file_info.original_filename,
            file_size=file_info.file_size,
            upload_time=file_info.upload_timestamp
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during file upload: {str(e)}"
        )

@router.post("/upload/multiple", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Multiple log files to upload"),
    description: Optional[str] = Form(None, description="Optional description for the files")
):
    """
    Upload multiple log files for analysis
    
    - **files**: List of log files (each supports .log, .txt, .json, .csv, .xml, .yaml formats)
    - **description**: Optional description for the files
    - **Max size per file**: 100MB
    - **Max files**: 10 files per request
    """
    
    # Limit number of files
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per request"
        )
    
    results = []
    
    for file in files:
        try:
            logger.info(f"Processing file: {file.filename}")
            
            # Save each file
            file_info = await file_service.save_uploaded_file(file)
            
            results.append(UploadResponse(
                success=True,
                message="File uploaded successfully",
                file_id=file_info.id,
                filename=file_info.original_filename,
                file_size=file_info.file_size,
                upload_time=file_info.upload_timestamp
            ))
            
        except HTTPException as e:
            # Add failed upload to results
            results.append(UploadResponse(
                success=False,
                message=f"Failed to upload {file.filename}: {e.detail}",
                filename=file.filename
            ))
        except Exception as e:
            results.append(UploadResponse(
                success=False,
                message=f"Unexpected error uploading {file.filename}: {str(e)}",
                filename=file.filename
            ))
    
    return results

@router.get("/upload/info/{file_id}")
async def get_file_info(file_id: str):
    """Get information about an uploaded file"""
    # This would typically query a database
    # For now, just check if file exists
    try:
        # In a real implementation, you'd query the database
        # For now, we'll return a basic response
        return {
            "file_id": file_id,
            "message": "File info endpoint - would query database in full implementation"
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_id}"
        )

@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file"""
    try:
        # In a real implementation, you'd:
        # 1. Query database for file info
        # 2. Delete file from disk
        # 3. Remove database record
        
        return {
            "success": True,
            "message": f"Delete endpoint for file {file_id} - would implement full deletion in production"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.get("/upload/formats")
async def get_supported_formats():
    """Get list of supported file formats and limits"""
    from app.models.upload import FileValidation
    
    return {
        "supported_extensions": FileValidation.ALLOWED_EXTENSIONS,
        "supported_mime_types": FileValidation.ALLOWED_MIME_TYPES,
        "max_file_size_mb": FileValidation.MAX_FILE_SIZE // (1024 * 1024),
        "max_files_per_request": 10
    }