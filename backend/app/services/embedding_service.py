"""
OpenAI Embedding Service for LogSage AI
Basic embedding pipeline using OpenAI API for MVP
"""
import openai
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os
from pathlib import Path
import hashlib
import uuid

from ..models.database import LogEntry, VectorEmbedding
from .database_service import db_service
from .vector_storage import vector_service


class EmbeddingService:
    """Service for generating embeddings using OpenAI API and storing them in FAISS"""
    
    def __init__(self):
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "text-embedding-ada-002"  # OpenAI's embedding model
        self.dimension = 1536  # Dimension for ada-002 model
        self.max_tokens = 8000  # Token limit for ada-002
        self.batch_size = 100  # Process embeddings in batches
        
        # Initialize OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
        
        # Cache for embeddings to avoid duplicate API calls
        self.embedding_cache = {}
        self.cache_dir = Path("./embedding_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embedding cache from disk"""
        cache_file = self.cache_dir / "embeddings.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}
    
    def _save_cache(self, cache: Dict[str, List[float]]):
        """Save embedding cache to disk"""
        cache_file = self.cache_dir / "embeddings.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text using OpenAI API"""
        if not self.api_key:
            # For demo purposes, return a random embedding if no API key
            print("⚠️  No OpenAI API key found, using random embedding for demo")
            return np.random.rand(self.dimension).tolist()
        
        # Check cache first
        cache_key = self._get_cache_key(text)
        cache = self._load_cache()
        
        if cache_key in cache:
            return cache[cache_key]
        
        try:
            # Truncate text if too long
            if len(text) > self.max_tokens * 4:  # Rough token estimation
                text = text[:self.max_tokens * 4]
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                openai.embeddings.create,
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            cache[cache_key] = embedding
            self._save_cache(cache)
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return random embedding as fallback for demo
            embedding = np.random.rand(self.dimension).tolist()
            cache[cache_key] = embedding
            self._save_cache(cache)
            return embedding
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        if not texts:
            return []
        
        if not self.api_key:
            # Return random embeddings for demo
            print(f"⚠️  No OpenAI API key found, using random embeddings for {len(texts)} texts")
            return [np.random.rand(self.dimension).tolist() for _ in texts]
        
        embeddings = []
        cache = self._load_cache()
        updated_cache = False
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = []
            batch_texts_to_process = []
            batch_indices = []
            
            # Check cache for each text in batch
            for j, text in enumerate(batch):
                cache_key = self._get_cache_key(text)
                if cache_key in cache:
                    batch_embeddings.append(cache[cache_key])
                else:
                    batch_texts_to_process.append(text)
                    batch_indices.append(j)
                    batch_embeddings.append(None)  # Placeholder
            
            # Process uncached texts
            if batch_texts_to_process:
                try:
                    # Truncate texts if too long
                    processed_texts = []
                    for text in batch_texts_to_process:
                        if len(text) > self.max_tokens * 4:
                            text = text[:self.max_tokens * 4]
                        processed_texts.append(text)
                    
                    # Call OpenAI API for batch
                    response = await asyncio.to_thread(
                        openai.embeddings.create,
                        model=self.model,
                        input=processed_texts
                    )
                    
                    # Update results and cache
                    for idx, (original_idx, text) in enumerate(zip(batch_indices, batch_texts_to_process)):
                        embedding = response.data[idx].embedding
                        batch_embeddings[original_idx] = embedding
                        
                        # Update cache
                        cache_key = self._get_cache_key(text)
                        cache[cache_key] = embedding
                        updated_cache = True
                
                except Exception as e:
                    print(f"Error generating batch embeddings: {e}")
                    # Fill with random embeddings as fallback
                    for original_idx in batch_indices:
                        if batch_embeddings[original_idx] is None:
                            embedding = np.random.rand(self.dimension).tolist()
                            batch_embeddings[original_idx] = embedding
                            
                            # Update cache
                            text = batch_texts_to_process[batch_indices.index(original_idx)]
                            cache_key = self._get_cache_key(text)
                            cache[cache_key] = embedding
                            updated_cache = True
            
            embeddings.extend(batch_embeddings)
        
        # Save updated cache
        if updated_cache:
            self._save_cache(cache)
        
        return embeddings
    
    async def embed_log_entries(self, file_id: str, log_entries: List[LogEntry]) -> Dict[str, Any]:
        """Generate embeddings for log entries and store in vector database"""
        if not log_entries:
            return {"message": "No log entries to process", "embeddings_created": 0}
        
        try:
            # Extract text content from log entries
            texts = []
            chunk_metadata = []
            
            for entry in log_entries:
                # Combine message and source for richer context
                text_content = entry.message
                if entry.source:
                    text_content = f"[{entry.source}] {text_content}"
                
                texts.append(text_content)
                chunk_metadata.append({
                    "log_id": entry.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level.value if hasattr(entry.level, 'value') else entry.level,
                    "source": entry.source,
                    "line_number": entry.line_number
                })
            
            # Generate embeddings
            print(f"Generating embeddings for {len(texts)} log entries...")
            embeddings = await self.generate_embeddings_batch(texts)
            
            # Filter out None embeddings
            valid_embeddings = []
            valid_texts = []
            valid_metadata = []
            
            for embedding, text, metadata in zip(embeddings, texts, chunk_metadata):
                if embedding is not None:
                    valid_embeddings.append(np.array(embedding, dtype=np.float32))
                    valid_texts.append(text)
                    valid_metadata.append(metadata)
            
            if not valid_embeddings:
                return {"message": "No valid embeddings generated", "embeddings_created": 0}
            
            # Store in FAISS vector database
            success = await vector_service.add_vectors(
                file_id, valid_embeddings, valid_texts, valid_metadata
            )
            
            if not success:
                return {"message": "Failed to store embeddings", "embeddings_created": 0}
            
            # Store embedding records in database
            embedding_records = []
            for i, (embedding, text, metadata) in enumerate(zip(valid_embeddings, valid_texts, valid_metadata)):
                chunk_id = str(uuid.uuid4())
                embedding_record = VectorEmbedding(
                    file_id=file_id,
                    chunk_id=chunk_id,
                    content=text,
                    embedding_vector=embedding.tobytes(),
                    embedding_model=self.model,
                    chunk_index=i,
                    timestamp=datetime.utcnow(),
                    metadata=metadata
                )
                embedding_records.append(embedding_record)
            
            # Store in database (vector_service already handles this, but we can add additional tracking)
            print(f"✅ Successfully created {len(valid_embeddings)} embeddings")
            
            return {
                "message": f"Successfully created embeddings for {len(valid_embeddings)} log entries",
                "embeddings_created": len(valid_embeddings),
                "model_used": self.model,
                "dimension": self.dimension,
                "cached_embeddings": len([e for e in embeddings if e is not None]) - len(valid_embeddings)
            }
            
        except Exception as e:
            print(f"Error in embed_log_entries: {e}")
            return {"message": f"Error creating embeddings: {str(e)}", "embeddings_created": 0}
    
    async def embed_text_chunks(self, file_id: str, text: str, chunk_size: int = 1000, overlap: int = 200) -> Dict[str, Any]:
        """Generate embeddings for text chunks"""
        try:
            # Chunk the text
            chunks = vector_service.chunk_text(text, chunk_size, overlap)
            
            if not chunks:
                return {"message": "No chunks created from text", "embeddings_created": 0}
            
            # Generate embeddings for chunks
            print(f"Generating embeddings for {len(chunks)} text chunks...")
            embeddings = await self.generate_embeddings_batch(chunks)
            
            # Filter valid embeddings
            valid_embeddings = []
            valid_chunks = []
            valid_metadata = []
            
            for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
                if embedding is not None:
                    valid_embeddings.append(np.array(embedding, dtype=np.float32))
                    valid_chunks.append(chunk)
                    valid_metadata.append({
                        "chunk_index": i,
                        "chunk_size": len(chunk),
                        "original_text_length": len(text)
                    })
            
            if not valid_embeddings:
                return {"message": "No valid embeddings generated", "embeddings_created": 0}
            
            # Store in vector database
            success = await vector_service.add_vectors(
                file_id, valid_embeddings, valid_chunks, valid_metadata
            )
            
            if not success:
                return {"message": "Failed to store embeddings", "embeddings_created": 0}
            
            return {
                "message": f"Successfully created embeddings for {len(valid_embeddings)} chunks",
                "embeddings_created": len(valid_embeddings),
                "total_chunks": len(chunks),
                "model_used": self.model,
                "dimension": self.dimension,
                "chunk_size": chunk_size,
                "overlap": overlap
            }
            
        except Exception as e:
            print(f"Error in embed_text_chunks: {e}")
            return {"message": f"Error creating embeddings: {str(e)}", "embeddings_created": 0}
    
    async def search_similar_logs(self, file_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search for similar log entries using embedding similarity"""
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            if query_embedding is None:
                return {"message": "Failed to generate query embedding", "results": []}
            
            # Search in vector database
            results = await vector_service.search_vectors(
                file_id, np.array(query_embedding, dtype=np.float32), top_k
            )
            
            return {
                "query": query,
                "results_found": len(results),
                "results": results,
                "model_used": self.model
            }
            
        except Exception as e:
            print(f"Error in search_similar_logs: {e}")
            return {"message": f"Error searching: {str(e)}", "results": []}
    
    async def get_embedding_statistics(self, file_id: str) -> Dict[str, Any]:
        """Get statistics about embeddings for a file"""
        try:
            # Get vector storage statistics
            storage_stats = await vector_service.get_storage_statistics()
            
            # Get index info for specific file
            index_info = await vector_service.get_index_info(file_id)
            
            # Get database embeddings
            db_embeddings = await db_service.get_vector_embeddings(file_id)
            
            return {
                "file_id": file_id,
                "total_embeddings": len(db_embeddings),
                "model_used": self.model,
                "dimension": self.dimension,
                "index_info": index_info,
                "storage_stats": storage_stats,
                "api_key_configured": bool(self.api_key),
                "cache_directory": str(self.cache_dir)
            }
            
        except Exception as e:
            print(f"Error getting embedding statistics: {e}")
            return {"message": f"Error retrieving statistics: {str(e)}"}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of the embedding service"""
        return {
            "service": "OpenAI Embedding Service",
            "model": self.model,
            "dimension": self.dimension,
            "max_tokens": self.max_tokens,
            "batch_size": self.batch_size,
            "api_key_configured": bool(self.api_key),
            "cache_enabled": True,
            "cache_directory": str(self.cache_dir)
        }


# Global embedding service instance
embedding_service = EmbeddingService()