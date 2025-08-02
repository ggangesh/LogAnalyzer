"""
Documentation Router for LogSage AI API

Provides comprehensive API documentation endpoints including:
- API information and metadata
- Endpoint groups and descriptions  
- Getting started guide
- Usage examples
- Status codes reference
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json

from ..services.documentation_service import documentation_service

router = APIRouter(prefix="/api/v1/docs", tags=["documentation"])

@router.get("/info", summary="Get API Information")
async def get_api_info() -> Dict[str, Any]:
    """
    Get comprehensive API information including version, contact details, and server information.
    
    Returns:
    - API title, version, and description
    - Documentation URLs (Swagger UI, ReDoc, OpenAPI)
    - Contact and license information
    - Available server endpoints
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_api_info(),
            "message": "API information retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API info: {str(e)}")

@router.get("/endpoints", summary="Get Endpoint Groups")
async def get_endpoint_groups() -> Dict[str, Any]:
    """
    Get organized endpoint groups with descriptions and available endpoints.
    
    Returns organized groups:
    - upload: File upload and management
    - log_analysis: Log parsing and time filtering  
    - database: SQLite database operations
    - anomaly: Anomaly detection and analysis
    - vectors: FAISS vector storage and search
    - embeddings: OpenAI embeddings pipeline
    - rag: Retrieval-Augmented Generation
    - chat: AI chat and conversation
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_endpoint_groups(),
            "message": "Endpoint groups retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get endpoint groups: {str(e)}")

@router.get("/getting-started", summary="Get Getting Started Guide")
async def get_getting_started_guide() -> Dict[str, Any]:
    """
    Get comprehensive getting started guide with step-by-step instructions.
    
    Returns:
    - Step-by-step workflow
    - API endpoint usage
    - cURL examples for each step
    - Best practices and tips
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_getting_started_guide(),
            "message": "Getting started guide retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get getting started guide: {str(e)}")

@router.get("/features", summary="Get API Features")
async def get_api_features() -> Dict[str, Any]:
    """
    Get comprehensive list of API features and capabilities.
    
    Returns:
    - Core features list
    - AI capabilities
    - Technical specifications
    - Supported formats and limits
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_api_features(),
            "message": "API features retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API features: {str(e)}")

@router.get("/examples", summary="Get API Usage Examples")
async def get_api_examples() -> Dict[str, Any]:
    """
    Get comprehensive API usage examples with request/response samples.
    
    Returns examples for:
    - File upload process
    - Log parsing and analysis
    - AI chat interactions
    - Error handling scenarios
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_examples(),
            "message": "API examples retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API examples: {str(e)}")

@router.get("/status-codes", summary="Get API Status Codes")
async def get_status_codes() -> Dict[str, Any]:
    """
    Get comprehensive list of API status codes and their meanings.
    
    Returns:
    - Success codes (2xx)
    - Client error codes (4xx)  
    - Server error codes (5xx)
    - Detailed descriptions for each code
    """
    try:
        return {
            "success": True,
            "data": documentation_service.get_status_codes(),
            "message": "Status codes retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status codes: {str(e)}")

@router.get("/health", summary="Documentation Service Health Check")
async def documentation_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the documentation service.
    
    Returns:
    - Service status
    - API version
    - Available documentation endpoints
    """
    try:
        return {
            "status": "healthy",
            "service": "LogSage AI Documentation",
            "version": documentation_service.version,
            "endpoints": [
                "/api/v1/docs/info",
                "/api/v1/docs/endpoints", 
                "/api/v1/docs/getting-started",
                "/api/v1/docs/features",
                "/api/v1/docs/examples",
                "/api/v1/docs/status-codes",
                "/api/v1/docs/health"
            ],
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Documentation service unhealthy: {str(e)}")

@router.get("/summary", summary="Get Complete Documentation Summary")
async def get_documentation_summary() -> Dict[str, Any]:
    """
    Get a complete documentation summary with all key information.
    
    Returns:
    - API overview and key features
    - Quick start workflow
    - All endpoint groups
    - Important examples
    - Status code reference
    """
    try:
        api_info = documentation_service.get_api_info()
        endpoint_groups = documentation_service.get_endpoint_groups()
        getting_started = documentation_service.get_getting_started_guide()
        features = documentation_service.get_api_features()
        examples = documentation_service.get_examples()
        status_codes = documentation_service.get_status_codes()
        
        return {
            "success": True,
            "data": {
                "api_info": api_info,
                "endpoint_groups": endpoint_groups,
                "getting_started": getting_started,
                "features": features,
                "examples": examples,
                "status_codes": status_codes
            },
            "message": "Complete documentation summary retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documentation summary: {str(e)}")

@router.get("/", summary="Documentation Index")
async def documentation_index() -> Dict[str, Any]:  
    """
    Documentation service index with links to all available documentation.
    
    Returns:
    - Available documentation endpoints
    - Quick links to Swagger UI and ReDoc
    - Service status and version
    """
    return {
        "service": "LogSage AI Documentation Service",
        "version": documentation_service.version,
        "description": "Comprehensive API documentation and guides",
        "documentation_endpoints": {
            "api_info": "/api/v1/docs/info",
            "endpoint_groups": "/api/v1/docs/endpoints",
            "getting_started": "/api/v1/docs/getting-started", 
            "features": "/api/v1/docs/features",
            "examples": "/api/v1/docs/examples",
            "status_codes": "/api/v1/docs/status-codes",
            "complete_summary": "/api/v1/docs/summary",
            "health_check": "/api/v1/docs/health"
        },
        "interactive_documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "quick_start": "Visit /api/v1/docs/getting-started for step-by-step guide"
    }