"""
SQLite Database Service for LogSage AI
"""
import sqlite3
import json
import pickle
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiosqlite
import asyncio
from ..models.database import LogEntry, FileMetadata, AnomalyDetection, VectorEmbedding, LogLevel


class DatabaseService:
    """SQLite database service for log management"""
    
    def __init__(self, db_path: str = "logsage.db"):
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        self.db_dir.mkdir(exist_ok=True)
    
    async def initialize_database(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create log_entries table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS log_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT,
                    raw_line TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    parsed_data TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create file_metadata table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    format_type TEXT NOT NULL,
                    upload_time DATETIME NOT NULL,
                    processing_status TEXT DEFAULT 'pending',
                    total_lines INTEGER,
                    parsed_lines INTEGER,
                    error_lines INTEGER,
                    processing_time REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create anomaly_detections table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    context TEXT,  -- JSON string
                    confidence_score REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create vector_embeddings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_vector BLOB NOT NULL,
                    embedding_model TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_log_entries_file_id ON log_entries(file_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_file_metadata_file_id ON file_metadata(file_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_detections_file_id ON anomaly_detections(file_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_vector_embeddings_file_id ON vector_embeddings(file_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_vector_embeddings_chunk_id ON vector_embeddings(chunk_id)")
            
            await db.commit()
    
    # File Metadata Operations
    async def create_file_metadata(self, metadata: FileMetadata) -> int:
        """Create file metadata record"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO file_metadata 
                (file_id, filename, file_path, file_size, format_type, upload_time, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.file_id, metadata.filename, metadata.file_path,
                metadata.file_size, metadata.format_type, metadata.upload_time,
                metadata.processing_status
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def update_file_metadata(self, file_id: str, **kwargs) -> bool:
        """Update file metadata"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [file_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE file_metadata 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE file_id = ?
            """, values)
            await db.commit()
            return True
    
    async def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata by file_id"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM file_metadata WHERE file_id = ?
            """, (file_id,))
            row = await cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                data = dict(zip(columns, row))
                return FileMetadata(**data)
            return None
    
    # Log Entry Operations
    async def create_log_entries(self, log_entries: List[LogEntry]) -> int:
        """Bulk insert log entries"""
        async with aiosqlite.connect(self.db_path) as db:
            entries_data = []
            for entry in log_entries:
                parsed_data_json = json.dumps(entry.parsed_data) if entry.parsed_data else None
                # Handle LogLevel - it could be enum or string
                level_value = entry.level.value if hasattr(entry.level, 'value') else entry.level
                entries_data.append((
                    entry.file_id, entry.timestamp, level_value,
                    entry.message, entry.source, entry.raw_line,
                    entry.line_number, parsed_data_json
                ))
            
            await db.executemany("""
                INSERT INTO log_entries 
                (file_id, timestamp, level, message, source, raw_line, line_number, parsed_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, entries_data)
            await db.commit()
            return len(entries_data)
    
    async def get_log_entries(self, file_id: str, limit: int = 1000, offset: int = 0) -> List[LogEntry]:
        """Get log entries for a file"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM log_entries 
                WHERE file_id = ? 
                ORDER BY timestamp DESC, line_number ASC
                LIMIT ? OFFSET ?
            """, (file_id, limit, offset))
            rows = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            entries = []
            for row in rows:
                data = dict(zip(columns, row))
                if data['parsed_data']:
                    data['parsed_data'] = json.loads(data['parsed_data'])
                entries.append(LogEntry(**data))
            return entries
    
    async def get_log_entries_by_time_range(
        self, file_id: str, start_time: datetime, end_time: datetime
    ) -> List[LogEntry]:
        """Get log entries within time range"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM log_entries 
                WHERE file_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (file_id, start_time, end_time))
            rows = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            entries = []
            for row in rows:
                data = dict(zip(columns, row))
                if data['parsed_data']:
                    data['parsed_data'] = json.loads(data['parsed_data'])
                entries.append(LogEntry(**data))
            return entries
    
    # Anomaly Detection Operations
    async def create_anomaly_detection(self, anomaly: AnomalyDetection) -> int:
        """Create anomaly detection record"""
        async with aiosqlite.connect(self.db_path) as db:
            context_json = json.dumps(anomaly.context) if anomaly.context else None
            cursor = await db.execute("""
                INSERT INTO anomaly_detections 
                (file_id, anomaly_type, timestamp, severity, description, context, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                anomaly.file_id, anomaly.anomaly_type, anomaly.timestamp,
                anomaly.severity, anomaly.description, context_json,
                anomaly.confidence_score
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_anomalies(self, file_id: str) -> List[AnomalyDetection]:
        """Get anomalies for a file"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM anomaly_detections 
                WHERE file_id = ? 
                ORDER BY timestamp DESC
            """, (file_id,))
            rows = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            anomalies = []
            for row in rows:
                data = dict(zip(columns, row))
                if data['context']:
                    data['context'] = json.loads(data['context'])
                anomalies.append(AnomalyDetection(**data))
            return anomalies
    
    # Vector Embedding Operations
    async def create_vector_embedding(self, embedding: VectorEmbedding) -> int:
        """Create vector embedding record"""
        async with aiosqlite.connect(self.db_path) as db:
            metadata_json = json.dumps(embedding.metadata) if embedding.metadata else None
            cursor = await db.execute("""
                INSERT INTO vector_embeddings 
                (file_id, chunk_id, content, embedding_vector, embedding_model, 
                 chunk_index, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                embedding.file_id, embedding.chunk_id, embedding.content,
                embedding.embedding_vector, embedding.embedding_model,
                embedding.chunk_index, embedding.timestamp, metadata_json
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_vector_embeddings(self, file_id: str) -> List[VectorEmbedding]:
        """Get vector embeddings for a file"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM vector_embeddings 
                WHERE file_id = ? 
                ORDER BY chunk_index ASC
            """, (file_id,))
            rows = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            embeddings = []
            for row in rows:
                data = dict(zip(columns, row))
                if data['metadata']:
                    data['metadata'] = json.loads(data['metadata'])
                embeddings.append(VectorEmbedding(**data))
            return embeddings
    
    # Statistics and Analytics
    async def get_log_statistics(self, file_id: str) -> Dict[str, Any]:
        """Get comprehensive log statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total counts by level
            cursor = await db.execute("""
                SELECT level, COUNT(*) as count 
                FROM log_entries 
                WHERE file_id = ? 
                GROUP BY level
            """, (file_id,))
            level_counts = dict(await cursor.fetchall())
            
            # Time range
            cursor = await db.execute("""
                SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time,
                       COUNT(*) as total_entries
                FROM log_entries 
                WHERE file_id = ?
            """, (file_id,))
            time_stats = await cursor.fetchone()
            
            # Source distribution
            cursor = await db.execute("""
                SELECT source, COUNT(*) as count 
                FROM log_entries 
                WHERE file_id = ? AND source IS NOT NULL 
                GROUP BY source 
                ORDER BY count DESC 
                LIMIT 10
            """, (file_id,))
            source_counts = dict(await cursor.fetchall())
            
            return {
                "level_distribution": level_counts,
                "total_entries": time_stats[2] if time_stats else 0,
                "time_range": {
                    "start": time_stats[0] if time_stats else None,
                    "end": time_stats[1] if time_stats else None
                },
                "source_distribution": source_counts
            }


# Global database service instance
db_service = DatabaseService()