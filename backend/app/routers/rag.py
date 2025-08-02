"""
RAG (Retrieval-Augmented Generation) API Router for LogSage AI
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.rag_service import rag_service
from ..services.database_service import db_service

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 10
    similarity_threshold: float = 0.3
    context_type: str = "full"  # "full", "chunks_only", "logs_only"


class ChunkDocumentRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    overlap: int = 200


class RAGConfigRequest(BaseModel):
    max_context_length: Optional[int] = None
    max_chunks: Optional[int] = None
    similarity_threshold: Optional[float] = None


@router.get("/status")
async def get_rag_service_status():
    """Get RAG service status and configuration"""
    try:
        # Get service configuration
        config = rag_service.update_rag_config()  # Returns current config
        
        return {
            "service": "RAG (Retrieval-Augmented Generation) Service",
            "status": "active",
            "configuration": config,
            "capabilities": [
                "Document chunking and embedding",
                "Vector similarity search",
                "Context preparation for generation",
                "Log-specific context retrieval",
                "Anomaly and error integration"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting RAG service status: {str(e)}")


@router.post("/query/{file_id}")
async def query_with_rag(file_id: str, request: RAGQueryRequest):
    """Query logs using RAG pipeline"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform RAG query
        result = await rag_service.query_logs_with_rag(
            file_id, 
            request.query,
            request.context_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/retrieve/{file_id}")
async def retrieve_relevant_chunks(file_id: str, request: RAGQueryRequest):
    """Retrieve relevant chunks for a query"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Retrieve chunks
        chunks = await rag_service.retrieve_relevant_chunks(
            file_id,
            request.query,
            request.top_k,
            request.similarity_threshold
        )
        
        return {
            "query": request.query,
            "file_id": file_id,
            "chunks_found": len(chunks),
            "top_k": request.top_k,
            "similarity_threshold": request.similarity_threshold,
            "chunks": [
                {
                    "content": chunk.content,
                    "similarity": chunk.similarity,
                    "chunk_id": chunk.chunk_id,
                    "metadata": chunk.metadata,
                    "timestamp": chunk.timestamp.isoformat() if chunk.timestamp else None
                }
                for chunk in chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk retrieval failed: {str(e)}")


@router.post("/context/{file_id}")
async def prepare_context(file_id: str, request: RAGQueryRequest):
    """Prepare RAG context for generation"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get RAG context
        context = await rag_service.retrieve_and_prepare_context(
            file_id, 
            request.query,
            request.top_k
        )
        
        return {
            "query": request.query,
            "file_id": file_id,
            "context": {
                "text": context.context_text,
                "chunks_retrieved": context.total_chunks,
                "chunks_used": len(context.retrieved_chunks),
                "max_similarity": context.max_similarity,
                "avg_similarity": context.avg_similarity,
                "context_length": len(context.context_text)
            },
            "chunks": [
                {
                    "content": chunk.content,
                    "similarity": chunk.similarity,
                    "chunk_id": chunk.chunk_id
                }
                for chunk in context.retrieved_chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context preparation failed: {str(e)}")


@router.post("/chunk/{file_id}")
async def chunk_and_embed_document(file_id: str, request: ChunkDocumentRequest):
    """Chunk a document and create embeddings for RAG"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Chunk and embed document
        result = await rag_service.chunk_and_embed_document(
            file_id,
            request.text,
            request.chunk_size,
            request.overlap
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document chunking failed: {str(e)}")


@router.get("/statistics/{file_id}")
async def get_rag_statistics(file_id: str):
    """Get RAG statistics for a file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        stats = await rag_service.get_rag_statistics(file_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving RAG statistics: {str(e)}")


@router.post("/config")
async def update_rag_config(request: RAGConfigRequest):
    """Update RAG configuration parameters"""
    try:
        config = rag_service.update_rag_config(
            max_context_length=request.max_context_length,
            max_chunks=request.max_chunks,
            similarity_threshold=request.similarity_threshold
        )
        
        return {
            "message": "RAG configuration updated successfully",
            "configuration": config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating RAG config: {str(e)}")


@router.get("/config")
async def get_rag_config():
    """Get current RAG configuration"""
    try:
        config = rag_service.update_rag_config()  # Returns current config without changes
        return {
            "configuration": config,
            "description": {
                "max_context_length": "Maximum characters in context for generation",
                "max_chunks": "Maximum number of chunks to retrieve",
                "similarity_threshold": "Minimum similarity score for chunk inclusion"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting RAG config: {str(e)}")


@router.get("/demo/{file_id}")
async def rag_demo(file_id: str, query: str = "What are the main issues in these logs?"):
    """Demo endpoint to showcase RAG capabilities"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform complete RAG pipeline demo
        result = await rag_service.retrieve_log_context(file_id, query)
        
        # Format for demo presentation
        demo_result = {
            "demo_query": query,
            "file_id": file_id,
            "filename": metadata.filename,
            "pipeline_steps": {
                "1_query_embedding": "Generated embedding for user query",
                "2_vector_search": f"Found {result.get('retrieval_stats', {}).get('chunks_retrieved', 0)} relevant chunks",
                "3_context_preparation": f"Prepared {result.get('retrieval_stats', {}).get('context_length', 0)} characters of context",
                "4_additional_context": "Added anomalies and error information"
            },
            "context_preview": result.get("rag_context", {}).get("context_text", "")[:500] + "...",
            "retrieval_stats": result.get("retrieval_stats", {}),
            "additional_context": result.get("additional_context", {}),
            "ready_for_generation": True
        }
        
        return demo_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG demo failed: {str(e)}")


@router.get("/health")
async def rag_health_check():
    """Health check for RAG service"""
    try:
        # Test basic functionality
        config = rag_service.update_rag_config()
        
        return {
            "service": "RAG Service",
            "status": "healthy",
            "configuration": config,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "service": "RAG Service", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }