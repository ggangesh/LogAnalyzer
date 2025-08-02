"""
Documentation Service for LogSage AI API

This service provides comprehensive API documentation, endpoint information,
and interactive documentation features.
"""

from typing import Dict, List, Any
from datetime import datetime
import json
from pathlib import Path

class DocumentationService:
    """Service for managing API documentation and information"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.title = "LogSage AI API"
        self.description = "AI-powered log analysis and monitoring system"
        
    def get_api_info(self) -> Dict[str, Any]:
        """Get comprehensive API information"""
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "documentation_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
            "contact": {
                "name": "LogSage AI Support",
                "email": "support@logsage.ai"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                }
            ]
        }
    
    def get_endpoint_groups(self) -> Dict[str, Any]:
        """Get organized endpoint groups with descriptions"""
        return {
            "upload": {
                "name": "File Upload",
                "description": "Endpoints for uploading and managing log files",
                "endpoints": [
                    "POST /api/v1/upload - Upload single log file",
                    "POST /api/v1/upload/multiple - Upload multiple log files",
                    "GET /api/v1/upload/info/{file_id} - Get file information",
                    "DELETE /api/v1/upload/{file_id} - Delete uploaded file",
                    "GET /api/v1/upload/formats - Get supported file formats"
                ]
            },
            "log_analysis": {
                "name": "Log Analysis",
                "description": "Core log parsing and time-based filtering",
                "endpoints": [
                    "GET /api/v1/logs/parse/{file_id} - Parse log file",
                    "GET /api/v1/logs/parse/{file_id}/format - Detect log format",
                    "GET /api/v1/logs/supported-formats - Get supported formats",
                    "GET /api/v1/logs/filters/quick - Get quick time filters",
                    "POST /api/v1/logs/filter/{file_id} - Filter logs by time",
                    "GET /api/v1/logs/insights/{file_id} - Get log insights",
                    "GET /api/v1/logs/statistics/{file_id} - Get log statistics"
                ]
            },
            "database": {
                "name": "Database Operations",
                "description": "SQLite database management and operations",
                "endpoints": [
                    "POST /api/v1/database/initialize - Initialize database",
                    "GET /api/v1/database/files/{file_id}/metadata - Get file metadata",
                    "GET /api/v1/database/files/{file_id}/logs - Get log entries",
                    "GET /api/v1/database/files/{file_id}/logs/time-range - Get logs by time range",
                    "GET /api/v1/database/files/{file_id}/statistics - Get database statistics"
                ]
            },
            "anomaly": {
                "name": "Anomaly Detection",
                "description": "Statistical anomaly detection and analysis",
                "endpoints": [
                    "POST /api/v1/anomaly/detect/{file_id} - Detect anomalies",
                    "GET /api/v1/anomaly/results/{file_id} - Get anomaly results",
                    "GET /api/v1/anomaly/summary/{file_id} - Get anomaly summary",
                    "GET /api/v1/anomaly/types - Get anomaly types"
                ]
            },
            "vectors": {
                "name": "Vector Storage",
                "description": "FAISS vector storage and similarity search",
                "endpoints": [
                    "POST /api/v1/vectors/initialize - Initialize vector storage",
                    "POST /api/v1/vectors/index/{file_id} - Create vector index",
                    "POST /api/v1/vectors/index/{file_id}/add - Add vectors to index",
                    "POST /api/v1/vectors/search/{file_id} - Search similar vectors",
                    "GET /api/v1/vectors/index/{file_id}/info - Get index info",
                    "GET /api/v1/vectors/indices - List all indices",
                    "GET /api/v1/vectors/statistics - Get storage statistics",
                    "POST /api/v1/vectors/chunk-text - Chunk text for processing"
                ]
            },
            "embeddings": {
                "name": "Embedding Pipeline",
                "description": "OpenAI embeddings generation and management",
                "endpoints": [
                    "GET /api/v1/embeddings/status - Get service status",
                    "POST /api/v1/embeddings/embed/logs/{file_id} - Embed log entries",
                    "POST /api/v1/embeddings/embed/text/{file_id} - Embed text chunks",
                    "POST /api/v1/embeddings/embed/single - Single text embedding",
                    "POST /api/v1/embeddings/search/{file_id} - Search similar logs",
                    "GET /api/v1/embeddings/statistics/{file_id} - Get embedding statistics",
                    "POST /api/v1/embeddings/batch - Batch embed texts",
                    "GET /api/v1/embeddings/models - Get available models",
                    "DELETE /api/v1/embeddings/cache - Clear embedding cache",
                    "GET /api/v1/embeddings/cache/statistics - Get cache statistics"
                ]
            },
            "rag": {
                "name": "RAG Pipeline",
                "description": "Retrieval-Augmented Generation for intelligent log analysis",
                "endpoints": [
                    "GET /api/v1/rag/status - Get RAG service status",
                    "POST /api/v1/rag/query/{file_id} - Complete RAG query",
                    "POST /api/v1/rag/retrieve/{file_id} - Retrieve relevant chunks",
                    "POST /api/v1/rag/context/{file_id} - Prepare RAG context",
                    "POST /api/v1/rag/chunk/{file_id} - Chunk and embed documents",
                    "GET /api/v1/rag/statistics/{file_id} - Get RAG statistics",
                    "POST /api/v1/rag/config - Update RAG configuration",
                    "GET /api/v1/rag/config - Get RAG configuration",
                    "GET /api/v1/rag/demo/{file_id} - RAG pipeline demo",
                    "GET /api/v1/rag/health - RAG health check"
                ]
            },
            "chat": {
                "name": "AI Chat Integration",
                "description": "GPT-4/4o integration for conversational AI and log analysis",
                "endpoints": [
                    "GET /api/v1/chat/status - Get chat service status",
                    "POST /api/v1/chat/message/{file_id} - Send chat message",
                    "POST /api/v1/chat/conversation/{file_id} - Continue conversation",
                    "POST /api/v1/chat/analyze/{file_id} - AI log analysis",
                    "POST /api/v1/chat/summary - Summarize conversation",
                    "GET /api/v1/chat/models - Get available models",
                    "GET /api/v1/chat/prompts - Get system prompts",
                    "GET /api/v1/chat/analysis-types - Get analysis types",
                    "POST /api/v1/chat/quick-ask/{file_id} - Quick question interface",
                    "GET /api/v1/chat/demo/{file_id} - Chat capabilities demo",
                    "GET /api/v1/chat/health - Chat health check"
                ]
            }
        }
    
    def get_getting_started_guide(self) -> Dict[str, Any]:
        """Get getting started guide for the API"""
        return {
            "title": "Getting Started with LogSage AI API",
            "steps": [
                {
                    "step": 1,
                    "title": "Upload a Log File",
                    "description": "Start by uploading a log file using the upload endpoint",
                    "endpoint": "POST /api/v1/upload",
                    "example": {
                        "curl": "curl -X POST 'http://localhost:8000/api/v1/upload' -F 'file=@your_log_file.log'"
                    }
                },
                {
                    "step": 2,
                    "title": "Parse and Analyze",
                    "description": "Parse the uploaded log file to extract structured data",
                    "endpoint": "GET /api/v1/logs/parse/{file_id}",
                    "example": {
                        "curl": "curl -X GET 'http://localhost:8000/api/v1/logs/parse/{file_id}'"
                    }
                },
                {
                    "step": 3,
                    "title": "Generate Embeddings",
                    "description": "Create embeddings for intelligent search and analysis",
                    "endpoint": "POST /api/v1/embeddings/embed/logs/{file_id}",
                    "example": {
                        "curl": "curl -X POST 'http://localhost:8000/api/v1/embeddings/embed/logs/{file_id}'"
                    }
                },
                {
                    "step": 4,
                    "title": "Ask Questions",
                    "description": "Use the AI chat interface to ask questions about your logs",
                    "endpoint": "POST /api/v1/chat/message/{file_id}",
                    "example": {
                        "curl": "curl -X POST 'http://localhost:8000/api/v1/chat/message/{file_id}' -H 'Content-Type: application/json' -d '{\"message\": \"What errors occurred in this log?\"}'"
                    }
                }
            ]
        }
    
    def get_api_features(self) -> Dict[str, Any]:
        """Get comprehensive list of API features"""
        return {
            "core_features": [
                "Multi-format log file parsing (JSON, CSV, XML, YAML, structured, plain text)",
                "Time-based filtering with predefined and custom ranges",
                "Statistical anomaly detection using multiple algorithms",
                "Vector embeddings with OpenAI integration",
                "FAISS-based similarity search and retrieval",
                "RAG (Retrieval-Augmented Generation) pipeline",
                "GPT-4/4o integration for conversational AI",
                "SQLite database for structured log storage",
                "Async operations for high performance",
                "Comprehensive error handling and validation"
            ],
            "ai_capabilities": [
                "Intelligent log analysis and summarization",
                "Anomaly detection with confidence scoring",
                "Semantic search across log entries",
                "Context-aware question answering",
                "Multiple analysis types (summary, errors, security, performance)",
                "Conversation history and multi-turn chat",
                "RAG-enhanced responses with relevant context"
            ],
            "technical_specifications": {
                "supported_formats": [".log", ".txt", ".json", ".csv", ".xml", ".yaml"],
                "max_file_size": "100MB",
                "embedding_model": "text-embedding-ada-002 (1536 dimensions)",
                "chat_models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"],
                "database": "SQLite with async operations",
                "vector_storage": "FAISS local index",
                "api_version": "v1"
            }
        }
    
    def get_examples(self) -> Dict[str, Any]:
        """Get API usage examples"""
        return {
            "upload_example": {
                "description": "Upload a log file",
                "method": "POST",
                "endpoint": "/api/v1/upload",
                "headers": {
                    "Content-Type": "multipart/form-data"
                },
                "body": "form-data with file field",
                "response": {
                    "file_id": "abc123",
                    "filename": "application.log",
                    "size": 1024,
                    "format": "structured",
                    "status": "uploaded"
                }
            },
            "parse_example": {
                "description": "Parse uploaded log file",
                "method": "GET", 
                "endpoint": "/api/v1/logs/parse/{file_id}",
                "response": {
                    "file_id": "abc123",
                    "total_entries": 150,
                    "format": "structured",
                    "entries": [
                        {
                            "timestamp": "2024-01-15T10:30:00Z",
                            "level": "ERROR",
                            "message": "Database connection failed",
                            "source": "database.py"
                        }
                    ]
                }
            },
            "chat_example": {
                "description": "Ask AI about log issues",
                "method": "POST",
                "endpoint": "/api/v1/chat/message/{file_id}",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "message": "What are the main errors in this log file?",
                    "use_rag": True
                },
                "response": {
                    "response": "Based on the log analysis, I found 3 main types of errors...",
                    "model": "gpt-4o-mini",
                    "rag_context_used": True,
                    "conversation_id": "conv_123"
                }
            }
        }
    
    def get_status_codes(self) -> Dict[str, Any]:
        """Get API status codes and their meanings"""
        return {
            "success_codes": {
                "200": "OK - Request successful",
                "201": "Created - Resource created successfully",
                "202": "Accepted - Request accepted for processing"
            },
            "client_error_codes": {
                "400": "Bad Request - Invalid request format",
                "401": "Unauthorized - Authentication required",
                "404": "Not Found - Resource not found",
                "413": "Payload Too Large - File too large",
                "422": "Unprocessable Entity - Validation error"
            },
            "server_error_codes": {
                "500": "Internal Server Error - Server error occurred",
                "503": "Service Unavailable - Service temporarily unavailable"
            }
        }

# Global documentation service instance
documentation_service = DocumentationService()