# LogSage AI Backend

FastAPI-based backend for AI-powered log analysis and monitoring system.

## Features Implemented

### ✅ B1 - FastAPI Project Structure
- Modular project structure with proper separation of concerns
- Comprehensive dependencies in requirements.txt
- Docker containerization with multi-stage builds
- Development-ready docker-compose configuration

### ✅ B2 - File Upload System
- Secure file upload with validation
- Support for multiple log formats (.log, .txt, .json, .csv, .xml, .yaml)
- 100MB file size limit
- Multiple file upload support
- Async file processing

## Quick Start

### Option 1: Docker (Recommended)
```bash
cd backend
docker-compose up --build
```

### Option 2: Local Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- **Health Check**: `GET /health`
- **Upload File**: `POST /api/v1/upload`
- **Upload Multiple Files**: `POST /api/v1/upload/multiple` 
- **Get File Info**: `GET /api/v1/upload/info/{file_id}`
- **Delete File**: `DELETE /api/v1/upload/{file_id}`
- **Supported Formats**: `GET /api/v1/upload/formats`

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## File Upload Specifications

- **Supported Formats**: .log, .txt, .json, .csv, .xml, .yaml, .yml
- **Maximum File Size**: 100MB per file
- **Multiple Upload Limit**: 10 files per request
- **Storage**: Files stored in `/uploads` directory with unique IDs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   └── upload.py        # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── upload.py        # Upload endpoints
│   └── services/
│       ├── __init__.py
│       └── file_service.py  # File handling logic
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Development setup
└── README.md               # This file
```

## Next Implementation Steps

Ready to implement:
- B3: Log parsing engine
- B4: Time-based filtering
- B5: Database schema
- B6: Anomaly detection
- And remaining tasks...