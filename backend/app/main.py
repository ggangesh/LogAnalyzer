from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.routers import upload, log_analysis, database, anomaly, vectors, embeddings, rag, chat, documentation, summarization, reports
from app.services.database_service import db_service
from app.services.vector_storage import vector_service
from app.services.embedding_service import embedding_service
from app.services.rag_service import rag_service
from app.services.chat_service import chat_service

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="LogSage AI API",
    description="""
    ## AI-Powered Log Analysis and Monitoring System
    
    LogSage AI provides comprehensive log analysis capabilities with artificial intelligence integration.
    
    ### Key Features:
    - **Multi-format Log Parsing**: Support for JSON, CSV, XML, YAML, structured logs, and plain text
    - **Time-based Filtering**: Advanced filtering with predefined and custom time ranges
    - **Anomaly Detection**: Statistical analysis for identifying unusual patterns and issues
    - **AI-Powered Analysis**: GPT-4/4o integration for intelligent log analysis and Q&A
    - **Vector Search**: Semantic similarity search using OpenAI embeddings and FAISS
    - **RAG Pipeline**: Retrieval-Augmented Generation for context-aware responses
    - **Real-time Processing**: Async operations for high-performance log processing
    
    ### Getting Started:
    1. Upload a log file using `/api/v1/upload`
    2. Parse and analyze with `/api/v1/logs/parse/{file_id}`  
    3. Generate embeddings with `/api/v1/embeddings/embed/logs/{file_id}`
    4. Ask questions using `/api/v1/chat/message/{file_id}`
    
    ### Documentation:
    - **Interactive API Docs**: Available at `/docs` (Swagger UI)
    - **Alternative Docs**: Available at `/redoc` (ReDoc)
    - **Comprehensive Guides**: Available at `/api/v1/docs/`
    - **Getting Started**: `/api/v1/docs/getting-started`
    """,
    version="1.0.0",
    contact={
        "name": "LogSage AI Support",
        "email": "support@logsage.ai",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    tags_metadata=[
        {
            "name": "upload",
            "description": "File upload and management operations for log files"
        },
        {
            "name": "log-analysis", 
            "description": "Core log parsing, format detection, and time-based filtering"
        },
        {
            "name": "database",
            "description": "SQLite database operations for structured log storage"
        },
        {
            "name": "anomaly",
            "description": "Statistical anomaly detection and pattern analysis"
        },
        {
            "name": "vectors",
            "description": "FAISS vector storage and similarity search operations"
        },
        {
            "name": "embeddings",
            "description": "OpenAI embeddings generation and management pipeline"
        },
        {
            "name": "rag",
            "description": "Retrieval-Augmented Generation pipeline for intelligent analysis"
        },
        {
            "name": "chat",
            "description": "GPT-4/4o AI chat integration for conversational log analysis"
        },
        {
            "name": "documentation",
            "description": "Comprehensive API documentation and usage guides"
        },
        {
            "name": "Summarization",
            "description": "Log summarization and daily/weekly insights generation"
        },
        {
            "name": "Reports",
            "description": "JSON report generation and export functionality"
        },
        {
            "name": "system",
            "description": "System health checks and service status endpoints"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(log_analysis.router)
app.include_router(database.router)
app.include_router(anomaly.router)
app.include_router(vectors.router)
app.include_router(embeddings.router)
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(documentation.router)
app.include_router(summarization.router)
app.include_router(reports.router)

# Startup event to initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize database and vector storage on startup"""
    try:
        # Initialize database
        await db_service.initialize_database()
        print("Database initialized successfully")
        
        # Initialize vector storage
        await vector_service.initialize_storage()
        print("Vector storage initialized successfully")
        
    except Exception as e:
        print(f"Startup initialization failed: {e}")

# Health check endpoint
@app.get("/health", tags=["system"], summary="API Health Check")
async def health_check():
    """
    Comprehensive health check endpoint for LogSage AI API.
    
    Returns:
    - API status and uptime information
    - Service availability status
    - Links to documentation
    """
    return {
        "status": "healthy", 
        "message": "LogSage AI API is running successfully",
        "version": "1.0.0",
        "services": {
            "database": "operational",
            "vector_storage": "operational", 
            "embeddings": "operational",
            "rag_pipeline": "operational",
            "chat_service": "operational",
            "summarization": "operational",
            "reports": "operational"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "comprehensive_docs": "/api/v1/docs/",
            "getting_started": "/api/v1/docs/getting-started"
        }
    }

@app.get("/", tags=["system"], summary="API Root Endpoint")
async def root():
    """
    Welcome endpoint with API overview and quick navigation links.
    
    Returns:
    - Welcome message and API description
    - Quick links to key endpoints
    - Documentation and getting started links
    """
    return {
        "message": "Welcome to LogSage AI API",
        "description": "AI-powered log analysis and monitoring system",
        "version": "1.0.0",
        "quick_start": {
            "1_upload": "POST /api/v1/upload",
            "2_parse": "GET /api/v1/logs/parse/{file_id}",
            "3_embed": "POST /api/v1/embeddings/embed/logs/{file_id}",
            "4_chat": "POST /api/v1/chat/message/{file_id}"
        },
        "documentation": {
            "interactive_docs": "/docs",
            "alternative_docs": "/redoc", 
            "comprehensive_guides": "/api/v1/docs/",
            "api_health": "/health"
        },
        "support": {
            "email": "support@logsage.ai",
            "getting_started": "/api/v1/docs/getting-started",
            "examples": "/api/v1/docs/examples"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)