"""
Vector Storage API Router for LogSage AI
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
import json

from ..services.vector_storage import vector_service
from ..services.database_service import db_service

router = APIRouter(prefix="/api/v1/vectors", tags=["vector-storage"])


class VectorSearchRequest(BaseModel):
    query_vector: List[float]
    top_k: int = 5


class ChunkTextRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    overlap: int = 200


@router.post("/initialize")
async def initialize_vector_storage():
    """Initialize vector storage"""
    try:
        await vector_service.initialize_storage()
        return {"message": "Vector storage initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector storage initialization failed: {str(e)}")


@router.post("/index/{file_id}")
async def create_vector_index(file_id: str, dimension: Optional[int] = None):
    """Create a new vector index for a file"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        success = await vector_service.create_index(file_id, dimension)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create vector index")
        
        return {"message": f"Vector index created for file {file_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating index: {str(e)}")


@router.post("/index/{file_id}/add")
async def add_vectors(
    file_id: str,
    vectors: List[List[float]],
    chunks: List[str],
    metadata: Optional[List[Dict[str, Any]]] = None
):
    """Add vectors to an existing index"""
    try:
        if len(vectors) != len(chunks):
            raise HTTPException(status_code=400, detail="Number of vectors must match number of chunks")
        
        # Convert to numpy arrays
        np_vectors = [np.array(v, dtype=np.float32) for v in vectors]
        
        success = await vector_service.add_vectors(file_id, np_vectors, chunks, metadata)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add vectors")
        
        return {
            "message": f"Added {len(vectors)} vectors to index for file {file_id}",
            "vectors_added": len(vectors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding vectors: {str(e)}")


@router.post("/search/{file_id}")
async def search_vectors(file_id: str, search_request: VectorSearchRequest):
    """Search for similar vectors"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        query_vector = np.array(search_request.query_vector, dtype=np.float32)
        results = await vector_service.search_vectors(file_id, query_vector, search_request.top_k)
        
        return {
            "file_id": file_id,
            "query_dimension": len(search_request.query_vector),
            "top_k": search_request.top_k,
            "results_found": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching vectors: {str(e)}")


@router.get("/index/{file_id}/info")
async def get_index_info(file_id: str):
    """Get information about a vector index"""
    try:
        info = await vector_service.get_index_info(file_id)
        if not info:
            raise HTTPException(status_code=404, detail="Vector index not found")
        
        return info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving index info: {str(e)}")


@router.get("/indices")
async def list_vector_indices():
    """List all available vector indices"""
    try:
        indices = await vector_service.list_indices()
        return {
            "total_indices": len(indices),
            "indices": indices
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing indices: {str(e)}")


@router.get("/chunk/{file_id}/{chunk_id}")
async def get_vector_by_chunk_id(file_id: str, chunk_id: str):
    """Get vector information by chunk ID"""
    try:
        chunk_info = await vector_service.get_vector_by_chunk_id(file_id, chunk_id)
        if not chunk_info:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        return chunk_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunk: {str(e)}")


@router.post("/chunk-text")
async def chunk_text(request: ChunkTextRequest):
    """Chunk text into smaller pieces for embedding"""
    try:
        chunks = vector_service.chunk_text(
            request.text, 
            request.chunk_size, 
            request.overlap
        )
        
        return {
            "original_length": len(request.text),
            "chunk_size": request.chunk_size,
            "overlap": request.overlap,
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "index": i,
                    "content": chunk,
                    "length": len(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chunking text: {str(e)}")


@router.get("/statistics")
async def get_storage_statistics():
    """Get vector storage statistics"""
    try:
        stats = await vector_service.get_storage_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.delete("/index/{file_id}")
async def delete_vector_index(file_id: str):
    """Delete a vector index and associated data"""
    try:
        success = await vector_service.delete_index(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete vector index")
        
        return {"message": f"Vector index deleted for file {file_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")


@router.get("/embeddings/{file_id}")
async def get_stored_embeddings(file_id: str):
    """Get stored embeddings from database"""
    try:
        embeddings = await db_service.get_vector_embeddings(file_id)
        
        return {
            "file_id": file_id,
            "total_embeddings": len(embeddings),
            "embeddings": [
                {
                    "id": emb.id,
                    "chunk_id": emb.chunk_id,
                    "content": emb.content[:200] + "..." if len(emb.content) > 200 else emb.content,
                    "content_length": len(emb.content),
                    "embedding_model": emb.embedding_model,
                    "chunk_index": emb.chunk_index,
                    "timestamp": emb.timestamp.isoformat(),
                    "metadata": emb.metadata
                }
                for emb in embeddings
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving embeddings: {str(e)}")