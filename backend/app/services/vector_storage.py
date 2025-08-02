"""
FAISS Vector Storage Service for LogSage AI
Simple local file storage for demo
"""
import faiss
import numpy as np
import pickle
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import hashlib

from ..models.database import VectorEmbedding
from .database_service import db_service


class VectorStorageService:
    """FAISS-based vector storage service for log embeddings"""
    
    def __init__(self, storage_dir: str = "vector_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # FAISS index parameters
        self.dimension = 1536  # OpenAI embedding dimension
        self.index_type = "flat"  # Simple flat index for demo
        
        # In-memory cache for loaded indices
        self._indices_cache = {}
        self._metadata_cache = {}
        
    async def initialize_storage(self):
        """Initialize vector storage directory structure"""
        # Create subdirectories
        (self.storage_dir / "indices").mkdir(exist_ok=True)
        (self.storage_dir / "metadata").mkdir(exist_ok=True)
        (self.storage_dir / "chunks").mkdir(exist_ok=True)
        
    def _get_file_paths(self, file_id: str) -> Dict[str, Path]:
        """Get file paths for a given file_id"""
        return {
            "index": self.storage_dir / "indices" / f"{file_id}.faiss",
            "metadata": self.storage_dir / "metadata" / f"{file_id}.json",
            "chunks": self.storage_dir / "chunks" / f"{file_id}.pkl"
        }
    
    async def create_index(self, file_id: str, dimension: int = None) -> bool:
        """Create a new FAISS index for a file"""
        try:
            if dimension is None:
                dimension = self.dimension
            
            # Create FAISS index
            if self.index_type == "flat":
                index = faiss.IndexFlatL2(dimension)
            else:
                # For larger datasets, could use IndexHNSWFlat or IndexIVFFlat
                index = faiss.IndexFlatL2(dimension)
            
            # Save index
            paths = self._get_file_paths(file_id)
            faiss.write_index(index, str(paths["index"]))
            
            # Initialize metadata
            metadata = {
                "file_id": file_id,
                "dimension": dimension,
                "total_vectors": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "embedding_model": "openai-text-embedding-ada-002",
                "chunks": []
            }
            
            with open(paths["metadata"], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Initialize empty chunks file
            with open(paths["chunks"], 'wb') as f:
                pickle.dump([], f)
            
            return True
            
        except Exception as e:
            print(f"Error creating index for {file_id}: {e}")
            return False
    
    async def add_vectors(
        self, 
        file_id: str, 
        vectors: List[np.ndarray], 
        chunks: List[str],
        chunk_metadata: List[Dict[str, Any]] = None
    ) -> bool:
        """Add vectors to FAISS index"""
        try:
            if len(vectors) != len(chunks):
                raise ValueError("Number of vectors must match number of chunks")
            
            paths = self._get_file_paths(file_id)
            
            # Load existing index
            if not paths["index"].exists():
                await self.create_index(file_id, vectors[0].shape[0] if vectors else self.dimension)
            
            index = faiss.read_index(str(paths["index"]))
            
            # Load existing metadata and chunks
            with open(paths["metadata"], 'r') as f:
                metadata = json.load(f)
            
            with open(paths["chunks"], 'rb') as f:
                existing_chunks = pickle.load(f)
            
            # Convert vectors to numpy array
            vector_array = np.array(vectors).astype('float32')
            
            # Add to index
            start_id = index.ntotal
            index.add(vector_array)
            
            # Update chunks and metadata
            new_chunks = []
            for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
                chunk_id = str(uuid.uuid4())
                chunk_info = {
                    "chunk_id": chunk_id,
                    "vector_id": start_id + i,
                    "content": chunk_text,
                    "chunk_index": len(existing_chunks) + i,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": chunk_metadata[i] if chunk_metadata else {}
                }
                new_chunks.append(chunk_info)
                existing_chunks.append(chunk_info)
                
                # Store in database
                embedding_data = VectorEmbedding(
                    file_id=file_id,
                    chunk_id=chunk_id,
                    content=chunk_text,
                    embedding_vector=vector.tobytes(),
                    embedding_model=metadata["embedding_model"],
                    chunk_index=chunk_info["chunk_index"],
                    timestamp=datetime.utcnow(),
                    metadata=chunk_metadata[i] if chunk_metadata else None
                )
                await db_service.create_vector_embedding(embedding_data)
            
            # Save updated index
            faiss.write_index(index, str(paths["index"]))
            
            # Update metadata
            metadata["total_vectors"] = index.ntotal
            metadata["updated_at"] = datetime.utcnow().isoformat()
            metadata["chunks"].extend([{
                "chunk_id": chunk["chunk_id"],
                "vector_id": chunk["vector_id"],
                "chunk_index": chunk["chunk_index"]
            } for chunk in new_chunks])
            
            with open(paths["metadata"], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save updated chunks
            with open(paths["chunks"], 'wb') as f:
                pickle.dump(existing_chunks, f)
            
            # Update cache
            if file_id in self._indices_cache:
                self._indices_cache[file_id] = index
                self._metadata_cache[file_id] = metadata
            
            return True
            
        except Exception as e:
            print(f"Error adding vectors for {file_id}: {e}")
            return False
    
    async def search_vectors(
        self, 
        file_id: str, 
        query_vector: np.ndarray, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            paths = self._get_file_paths(file_id)
            
            if not paths["index"].exists():
                return []
            
            # Load index and metadata
            if file_id not in self._indices_cache:
                index = faiss.read_index(str(paths["index"]))
                with open(paths["metadata"], 'r') as f:
                    metadata = json.load(f)
                with open(paths["chunks"], 'rb') as f:
                    chunks = pickle.load(f)
                
                self._indices_cache[file_id] = index
                self._metadata_cache[file_id] = {"metadata": metadata, "chunks": chunks}
            else:
                index = self._indices_cache[file_id]
                data = self._metadata_cache[file_id]
                metadata = data["metadata"]
                chunks = data["chunks"]
            
            # Ensure query vector is the right shape and type
            query_vector = np.array([query_vector]).astype('float32')
            
            # Search
            distances, indices = index.search(query_vector, min(top_k, index.ntotal))
            
            # Build results
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx < len(chunks):
                    chunk_info = chunks[idx]
                    results.append({
                        "chunk_id": chunk_info["chunk_id"],
                        "content": chunk_info["content"],
                        "distance": float(distance),
                        "similarity": 1 / (1 + float(distance)),  # Convert distance to similarity
                        "chunk_index": chunk_info["chunk_index"],
                        "metadata": chunk_info.get("metadata", {}),
                        "timestamp": chunk_info["timestamp"]
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching vectors for {file_id}: {e}")
            return []
    
    async def get_vector_by_chunk_id(self, file_id: str, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get vector information by chunk ID"""
        try:
            paths = self._get_file_paths(file_id)
            
            if not paths["chunks"].exists():
                return None
            
            with open(paths["chunks"], 'rb') as f:
                chunks = pickle.load(f)
            
            for chunk in chunks:
                if chunk["chunk_id"] == chunk_id:
                    return chunk
            
            return None
            
        except Exception as e:
            print(f"Error getting vector by chunk ID: {e}")
            return None
    
    async def delete_index(self, file_id: str) -> bool:
        """Delete FAISS index and associated data"""
        try:
            paths = self._get_file_paths(file_id)
            
            # Remove from cache
            if file_id in self._indices_cache:
                del self._indices_cache[file_id]
            if file_id in self._metadata_cache:
                del self._metadata_cache[file_id]
            
            # Delete files
            for path in paths.values():
                if path.exists():
                    path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting index for {file_id}: {e}")
            return False
    
    async def get_index_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an index"""
        try:
            paths = self._get_file_paths(file_id)
            
            if not paths["metadata"].exists():
                return None
            
            with open(paths["metadata"], 'r') as f:
                metadata = json.load(f)
            
            # Add file size information
            file_sizes = {}
            for name, path in paths.items():
                if path.exists():
                    file_sizes[f"{name}_size_bytes"] = path.stat().st_size
            
            metadata.update(file_sizes)
            return metadata
            
        except Exception as e:
            print(f"Error getting index info for {file_id}: {e}")
            return None
    
    async def list_indices(self) -> List[str]:
        """List all available indices"""
        try:
            indices_dir = self.storage_dir / "indices"
            if not indices_dir.exists():
                return []
            
            file_ids = []
            for index_file in indices_dir.glob("*.faiss"):
                file_ids.append(index_file.stem)
            
            return file_ids
            
        except Exception as e:
            print(f"Error listing indices: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking for embeddings"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or word boundaries
            if end < len(text):
                # Look for sentence boundary
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                boundary = max(last_period, last_newline)
                
                if boundary > start + chunk_size // 2:  # If boundary is reasonable
                    end = boundary + 1
                else:
                    # Look for word boundary
                    last_space = text.rfind(' ', start, end)
                    if last_space > start + chunk_size // 2:
                        end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            indices = await self.list_indices()
            total_size = 0
            total_vectors = 0
            
            for file_id in indices:
                info = await self.get_index_info(file_id)
                if info:
                    total_vectors += info.get("total_vectors", 0)
                    total_size += info.get("index_size_bytes", 0)
                    total_size += info.get("metadata_size_bytes", 0)
                    total_size += info.get("chunks_size_bytes", 0)
            
            return {
                "total_indices": len(indices),
                "total_vectors": total_vectors,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_directory": str(self.storage_dir),
                "indices": indices
            }
            
        except Exception as e:
            print(f"Error getting storage statistics: {e}")
            return {
                "total_indices": 0,
                "total_vectors": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "storage_directory": str(self.storage_dir),
                "indices": []
            }


# Global vector storage service instance
vector_service = VectorStorageService()