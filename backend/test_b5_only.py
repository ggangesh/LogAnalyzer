"""
Simple B5 test to debug database issues
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.database import LogEntry, FileMetadata, LogLevel
from app.services.database_service import db_service

async def test_b5():
    try:
        print("🧪 Testing B5: SQLite Database Schema...")
        
        # Initialize database
        await db_service.initialize_database()
        print("✅ Database initialized")
        
        # Create unique file ID
        unique_file_id = f"test_b5_file_{uuid.uuid4().hex[:8]}"
        print(f"Using file_id: {unique_file_id}")
        
        # Test file metadata creation
        test_metadata = FileMetadata(
            file_id=unique_file_id,
            filename="test.log",
            file_path="/uploads/test.log",
            file_size=1024,
            format_type="structured",
            upload_time=datetime.utcnow(),
            processing_status="completed"
        )
        
        metadata_id = await db_service.create_file_metadata(test_metadata)
        print(f"✅ File metadata created with ID: {metadata_id}")
        
        # Test log entries creation (just a few)
        test_entries = []
        for i in range(3):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                level=LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR,
                message=f"Test log message {i}",
                source="test_service",
                raw_line=f"[INFO] Test log message {i}",
                line_number=i + 1,
                parsed_data={"test": True, "index": i}
            )
            test_entries.append(entry)
        
        print(f"Creating {len(test_entries)} log entries...")
        entries_count = await db_service.create_log_entries(test_entries)
        print(f"✅ Created {entries_count} log entries")
        
        # Test retrieval
        retrieved_entries = await db_service.get_log_entries(unique_file_id, limit=5)
        print(f"✅ Retrieved {len(retrieved_entries)} log entries")
        
        # Test statistics
        stats = await db_service.get_log_statistics(unique_file_id)
        print(f"✅ Statistics: {stats['total_entries']} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ B5 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_b5())
    if result:
        print("🎉 B5 test PASSED!")
    else:
        print("❌ B5 test FAILED!")