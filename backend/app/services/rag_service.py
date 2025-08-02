"""
RAG (Retrieval-Augmented Generation) Service for LogSage AI
Simple RAG pipeline with basic chunking and retrieval for demo
"""
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re
from dataclasses import dataclass

from ..models.database import LogEntry
from .database_service import db_service
from .embedding_service import embedding_service
from .vector_storage import vector_service


@dataclass
class RetrievalResult:
    """Represents a retrieved document/chunk for RAG"""
    content: str
    similarity: float
    metadata: Dict[str, Any]
    chunk_id: str
    file_id: str
    timestamp: Optional[datetime] = None


@dataclass
class RAGContext:
    """Context prepared for generation"""
    query: str
    retrieved_chunks: List[RetrievalResult]
    context_text: str
    total_chunks: int
    max_similarity: float
    avg_similarity: float


class RAGService:
    """Service for Retrieval-Augmented Generation pipeline"""
    
    def __init__(self):
        self.max_context_length = 4000  # Max context chars for generation
        self.max_chunks = 10  # Max chunks to retrieve
        self.similarity_threshold = 0.3  # Minimum similarity for inclusion
        self.chunk_separator = "\n---\n"  # Separator between chunks
        
    async def retrieve_relevant_chunks(
        self, 
        file_id: str, 
        query: str, 
        top_k: int = None,
        similarity_threshold: float = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query using vector similarity"""
        if top_k is None:
            top_k = self.max_chunks
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        try:
            # Generate embedding for the query
            query_embedding = await embedding_service.generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Search for similar vectors
            search_results = await vector_service.search_vectors(
                file_id, 
                np.array(query_embedding, dtype=np.float32), 
                top_k
            )
            
            # Convert to RetrievalResult objects and filter by similarity
            retrieval_results = []
            for result in search_results:
                similarity = result.get("similarity", 0.0)
                
                # Convert distance to similarity if needed
                if "distance" in result:
                    # FAISS returns L2 distance, convert to similarity
                    distance = result["distance"]
                    similarity = 1 / (1 + distance)
                
                if similarity >= similarity_threshold:
                    retrieval_result = RetrievalResult(
                        content=result["content"],
                        similarity=similarity,
                        metadata=result.get("metadata", {}),
                        chunk_id=result["chunk_id"],
                        file_id=file_id,
                        timestamp=datetime.fromisoformat(result["timestamp"]) if result.get("timestamp") else None
                    )
                    retrieval_results.append(retrieval_result)
            
            # Sort by similarity (highest first)
            retrieval_results.sort(key=lambda x: x.similarity, reverse=True)
            
            return retrieval_results
            
        except Exception as e:
            print(f"Error in retrieve_relevant_chunks: {e}")
            return []
    
    async def prepare_rag_context(
        self, 
        query: str, 
        retrieved_chunks: List[RetrievalResult]
    ) -> RAGContext:
        """Prepare context for generation from retrieved chunks"""
        if not retrieved_chunks:
            return RAGContext(
                query=query,
                retrieved_chunks=[],
                context_text="No relevant information found.",
                total_chunks=0,
                max_similarity=0.0,
                avg_similarity=0.0
            )
        
        # Calculate similarity statistics
        similarities = [chunk.similarity for chunk in retrieved_chunks]
        max_similarity = max(similarities)
        avg_similarity = sum(similarities) / len(similarities)
        
        # Build context text with smart truncation
        context_parts = []
        current_length = 0
        included_chunks = []
        
        for chunk in retrieved_chunks:
            chunk_text = self._format_chunk_for_context(chunk)
            chunk_length = len(chunk_text)
            
            # Check if adding this chunk would exceed context limit
            if current_length + chunk_length + len(self.chunk_separator) > self.max_context_length:
                # Try to fit a truncated version
                remaining_space = self.max_context_length - current_length - len(self.chunk_separator) - 20  # Buffer
                if remaining_space > 100:  # Only truncate if meaningful space left
                    truncated_chunk = chunk_text[:remaining_space] + "..."
                    context_parts.append(truncated_chunk)
                    included_chunks.append(chunk)
                break
            
            context_parts.append(chunk_text)
            current_length += chunk_length + len(self.chunk_separator)
            included_chunks.append(chunk)
        
        context_text = self.chunk_separator.join(context_parts)
        
        return RAGContext(
            query=query,
            retrieved_chunks=included_chunks,
            context_text=context_text,
            total_chunks=len(retrieved_chunks),
            max_similarity=max_similarity,
            avg_similarity=avg_similarity
        )
    
    def _format_chunk_for_context(self, chunk: RetrievalResult) -> str:
        """Format a chunk for inclusion in generation context"""
        metadata = chunk.metadata
        
        # Add metadata context if available
        context_parts = []
        
        if metadata.get("timestamp"):
            context_parts.append(f"Time: {metadata['timestamp']}")
        
        if metadata.get("level"):
            context_parts.append(f"Level: {metadata['level']}")
        
        if metadata.get("source"):
            context_parts.append(f"Source: {metadata['source']}")
        
        if metadata.get("line_number"):
            context_parts.append(f"Line: {metadata['line_number']}")
        
        # Format the chunk
        header = f"[Similarity: {chunk.similarity:.3f}]"
        if context_parts:
            header += f" [{', '.join(context_parts)}]"
        
        return f"{header}\n{chunk.content}"
    
    async def retrieve_and_prepare_context(
        self, 
        file_id: str, 
        query: str, 
        top_k: int = None
    ) -> RAGContext:
        """Complete RAG retrieval pipeline: retrieve chunks and prepare context"""
        # Retrieve relevant chunks
        retrieved_chunks = await self.retrieve_relevant_chunks(file_id, query, top_k)
        
        # Prepare context for generation
        context = await self.prepare_rag_context(query, retrieved_chunks)
        
        return context
    
    async def retrieve_log_context(
        self, 
        file_id: str, 
        query: str, 
        include_anomalies: bool = True,
        include_errors: bool = True
    ) -> Dict[str, Any]:
        """Retrieve log-specific context with optional filtering"""
        try:
            # Get basic RAG context
            rag_context = await self.retrieve_and_prepare_context(file_id, query)
            
            # Get additional log-specific context
            additional_context = {}
            
            if include_anomalies:
                # Get anomalies from database
                anomalies = await db_service.get_anomalies(file_id)
                if anomalies:
                    anomaly_summaries = []
                    for anomaly in anomalies[:5]:  # Top 5 anomalies
                        summary = f"{anomaly.anomaly_type} ({anomaly.severity}): {anomaly.description}"
                        anomaly_summaries.append(summary)
                    additional_context["anomalies"] = anomaly_summaries
            
            if include_errors:
                # Get recent error entries
                log_entries = await db_service.get_log_entries(file_id, limit=100)
                error_entries = [
                    entry for entry in log_entries 
                    if hasattr(entry.level, 'value') and entry.level.value in ['ERROR', 'CRITICAL']
                    or (isinstance(entry.level, str) and entry.level in ['ERROR', 'CRITICAL'])
                ][:10]  # Top 10 errors
                
                if error_entries:
                    error_messages = [f"{entry.timestamp}: {entry.message}" for entry in error_entries]
                    additional_context["recent_errors"] = error_messages
            
            return {
                "query": query,
                "file_id": file_id,
                "rag_context": rag_context,
                "additional_context": additional_context,
                "retrieval_stats": {
                    "chunks_retrieved": rag_context.total_chunks,
                    "chunks_used": len(rag_context.retrieved_chunks),
                    "max_similarity": rag_context.max_similarity,
                    "avg_similarity": rag_context.avg_similarity,
                    "context_length": len(rag_context.context_text)
                }
            }
            
        except Exception as e:
            print(f"Error in retrieve_log_context: {e}")
            return {
                "query": query,
                "file_id": file_id,
                "error": str(e),
                "rag_context": RAGContext(
                    query=query,
                    retrieved_chunks=[],
                    context_text="Error retrieving context.",
                    total_chunks=0,
                    max_similarity=0.0,
                    avg_similarity=0.0
                )
            }
    
    async def chunk_and_embed_document(
        self, 
        file_id: str, 
        document_text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200
    ) -> Dict[str, Any]:
        """Chunk a document and create embeddings for RAG retrieval"""
        try:
            # Use the embedding service to chunk and embed the document
            result = await embedding_service.embed_text_chunks(
                file_id, document_text, chunk_size, overlap
            )
            
            return {
                "file_id": file_id,
                "document_length": len(document_text),
                "chunk_size": chunk_size,
                "overlap": overlap,
                **result
            }
            
        except Exception as e:
            print(f"Error in chunk_and_embed_document: {e}")
            return {
                "file_id": file_id,
                "error": str(e),
                "embeddings_created": 0
            }
    
    async def get_rag_statistics(self, file_id: str) -> Dict[str, Any]:
        """Get RAG-related statistics for a file"""
        try:
            # Get vector storage statistics
            vector_stats = await vector_service.get_index_info(file_id)
            
            # Get embedding statistics
            embedding_stats = await embedding_service.get_embedding_statistics(file_id)
            
            # Get log statistics
            log_stats = await db_service.get_log_statistics(file_id)
            
            return {
                "file_id": file_id,
                "vector_storage": vector_stats,
                "embeddings": embedding_stats,
                "logs": log_stats,
                "rag_config": {
                    "max_context_length": self.max_context_length,
                    "max_chunks": self.max_chunks,
                    "similarity_threshold": self.similarity_threshold
                }
            }
            
        except Exception as e:
            print(f"Error getting RAG statistics: {e}")
            return {
                "file_id": file_id,
                "error": str(e)
            }
    
    def update_rag_config(
        self, 
        max_context_length: int = None,
        max_chunks: int = None,
        similarity_threshold: float = None
    ) -> Dict[str, Any]:
        """Update RAG configuration parameters"""
        if max_context_length is not None:
            self.max_context_length = max_context_length
        
        if max_chunks is not None:
            self.max_chunks = max_chunks
        
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        
        return {
            "max_context_length": self.max_context_length,
            "max_chunks": self.max_chunks,
            "similarity_threshold": self.similarity_threshold
        }
    
    async def query_logs_with_rag(
        self, 
        file_id: str, 
        query: str,
        context_type: str = "full"  # "full", "chunks_only", "logs_only"
    ) -> Dict[str, Any]:
        """Main RAG query interface for log analysis"""
        try:
            if context_type == "chunks_only":
                # Only vector similarity context
                rag_context = await self.retrieve_and_prepare_context(file_id, query)
                return {
                    "query": query,
                    "file_id": file_id,
                    "context_type": context_type,
                    "context": rag_context.context_text,
                    "retrieval_stats": {
                        "chunks_retrieved": rag_context.total_chunks,
                        "max_similarity": rag_context.max_similarity,
                        "avg_similarity": rag_context.avg_similarity
                    }
                }
            
            elif context_type == "logs_only":
                # Direct log database query
                log_entries = await db_service.get_log_entries(file_id, limit=50)
                context_text = "\n".join([
                    f"[{entry.timestamp}] {entry.level}: {entry.message}"
                    for entry in log_entries[:20]  # Limit for context
                ])
                
                return {
                    "query": query,
                    "file_id": file_id,
                    "context_type": context_type,
                    "context": context_text,
                    "log_count": len(log_entries)
                }
            
            else:  # "full"
                # Complete RAG context with logs, anomalies, etc.
                full_context = await self.retrieve_log_context(file_id, query)
                return {
                    "query": query,
                    "file_id": file_id,
                    "context_type": context_type,
                    **full_context
                }
                
        except Exception as e:
            print(f"Error in query_logs_with_rag: {e}")
            return {
                "query": query,
                "file_id": file_id,
                "error": str(e)
            }


# Global RAG service instance
rag_service = RAGService()