"""
Embeddings API Router for LogSage AI
OpenAI embedding pipeline endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..services.embedding_service import embedding_service
from ..services.database_service import db_service
from ..services.log_parser import LogParser

# Initialize log parser
log_parser = LogParser()

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])


class EmbedLogEntriesRequest(BaseModel):
    file_id: str
    force_reembed: bool = False


class EmbedTextRequest(BaseModel):
    file_id: str
    text: str
    chunk_size: int = 1000
    overlap: int = 200


class SearchSimilarRequest(BaseModel):
    query: str
    top_k: int = 5


@router.get("/status")
async def get_embedding_service_status():
    """Get the status of the embedding service"""
    try:
        status = embedding_service.get_service_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting service status: {str(e)}")


@router.post("/embed/logs/{file_id}")
async def embed_log_entries(file_id: str, background_tasks: BackgroundTasks, force_reembed: bool = False):
    """Generate embeddings for log entries in a file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get log entries from database
        log_entries = await db_service.get_log_entries(file_id, limit=10000)  # Limit for demo
        
        if not log_entries:
            # Try to get from parser if not in database
            parsed_result = log_parser.parse_file(metadata.file_path)
            if parsed_result and parsed_result.entries:
                # Convert parsed entries to LogEntry objects
                from datetime import datetime
                from ..models.database import LogEntry, LogLevel
                
                log_entries = []
                for parser_entry in parsed_result.entries:
                    # Handle None level
                    level = None
                    if parser_entry.level:
                        try:
                            level = LogLevel(parser_entry.level.upper())
                        except ValueError:
                            level = LogLevel.INFO  # Default fallback
                    
                    log_entry = LogEntry(
                        file_id=file_id,
                        timestamp=parser_entry.timestamp,
                        level=level,
                        message=parser_entry.message,
                        source=parser_entry.source,
                        raw_line=parser_entry.raw_line,
                        line_number=parser_entry.line_number,
                        parsed_data=parser_entry.parsed_data
                    )
                    log_entries.append(log_entry)
                
                # Store in database
                if log_entries:
                    await db_service.create_log_entries(log_entries)
            
            if not log_entries:
                raise HTTPException(status_code=400, detail="No log entries found to embed")
        
        # Generate embeddings
        result = await embedding_service.embed_log_entries(file_id, log_entries)
        
        # Update file metadata
        await db_service.update_file_metadata(
            file_id, 
            embedding_status="completed",
            embedding_count=result.get("embeddings_created", 0)
        )
        
        return {
            "file_id": file_id,
            "total_log_entries": len(log_entries),
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/embed/text/{file_id}")
async def embed_text_chunks(file_id: str, request: EmbedTextRequest):
    """Generate embeddings for text chunks"""
    try:
        result = await embedding_service.embed_text_chunks(
            request.file_id,
            request.text,
            request.chunk_size,
            request.overlap
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text embedding failed: {str(e)}")


@router.post("/embed/single")
async def embed_single_text(text: str):
    """Generate embedding for a single text (for testing/demo)"""
    try:
        embedding = await embedding_service.generate_embedding(text)
        
        if embedding is None:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "embedding_dimension": len(embedding),
            "model_used": embedding_service.model,
            "embedding": embedding[:10] + ["..."] if len(embedding) > 10 else embedding  # Show first 10 values
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Single text embedding failed: {str(e)}")


@router.post("/search/{file_id}")
async def search_similar_logs(file_id: str, request: SearchSimilarRequest):
    """Search for similar log entries using embedding similarity"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        result = await embedding_service.search_similar_logs(
            file_id, request.query, request.top_k
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


@router.get("/statistics/{file_id}")
async def get_embedding_statistics(file_id: str):
    """Get embedding statistics for a file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        stats = await embedding_service.get_embedding_statistics(file_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.get("/models")
async def get_available_models():
    """Get information about available embedding models"""
    return {
        "current_model": embedding_service.model,
        "available_models": [
            {
                "name": "text-embedding-ada-002",
                "dimension": 1536,
                "max_tokens": 8000,
                "description": "OpenAI's most capable embedding model (current)"
            },
            {
                "name": "text-embedding-3-small",
                "dimension": 1536,
                "max_tokens": 8000,
                "description": "Newer, more efficient embedding model (if available)"
            },
            {
                "name": "text-embedding-3-large",
                "dimension": 3072,
                "max_tokens": 8000,
                "description": "Highest capability embedding model (if available)"
            }
        ],
        "note": "Currently using ada-002 for MVP compatibility"
    }


@router.delete("/cache")
async def clear_embedding_cache():
    """Clear the embedding cache (admin endpoint)"""
    try:
        import os
        cache_file = embedding_service.cache_dir / "embeddings.json"
        
        if cache_file.exists():
            os.remove(cache_file)
            return {"message": "Embedding cache cleared successfully"}
        else:
            return {"message": "No cache file found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/cache/statistics")
async def get_cache_statistics():
    """Get embedding cache statistics"""
    try:
        cache = embedding_service._load_cache()
        cache_file = embedding_service.cache_dir / "embeddings.json"
        
        file_size = 0
        if cache_file.exists():
            file_size = cache_file.stat().st_size
        
        return {
            "cached_embeddings": len(cache),
            "cache_file_size_bytes": file_size,
            "cache_file_size_mb": round(file_size / (1024 * 1024), 2),
            "cache_directory": str(embedding_service.cache_dir),
            "estimated_api_calls_saved": len(cache)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cache statistics: {str(e)}")


@router.post("/batch")
async def embed_batch_texts(texts: List[str], max_texts: int = 100):
    """Generate embeddings for multiple texts (batch processing)"""
    try:
        if len(texts) > max_texts:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many texts. Maximum allowed: {max_texts}"
            )
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        embeddings = await embedding_service.generate_embeddings_batch(texts)
        
        # Count successful embeddings
        successful_embeddings = [e for e in embeddings if e is not None]
        
        return {
            "total_texts": len(texts),
            "successful_embeddings": len(successful_embeddings),
            "failed_embeddings": len(texts) - len(successful_embeddings),
            "model_used": embedding_service.model,
            "dimension": embedding_service.dimension,
            "embeddings": [
                {
                    "text": text[:50] + "..." if len(text) > 50 else text,
                    "embedding_preview": embedding[:5] + ["..."] if embedding and len(embedding) > 5 else embedding,
                    "success": embedding is not None
                }
                for text, embedding in zip(texts, embeddings)
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding failed: {str(e)}")