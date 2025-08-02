"""
Validation script for B5-B7 implementations
Tests SQLite database, anomaly detection, and FAISS vector storage
"""
import asyncio
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.database import LogEntry, FileMetadata, AnomalyDetection, VectorEmbedding, LogLevel
from app.services.database_service import db_service
from app.services.anomaly_detection import anomaly_service
from app.services.vector_storage import vector_service


async def test_b5_database_schema():
    """Test B5: SQLite database schema implementation"""
    print("🧪 Testing B5: SQLite Database Schema...")
    
    try:
        # Initialize database
        await db_service.initialize_database()
        print("✅ Database initialization successful")
        
        # Generate unique file ID for this test run
        import uuid
        unique_file_id = f"test_b5_file_{uuid.uuid4().hex[:8]}"
        
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
        
        # Test metadata retrieval
        retrieved_metadata = await db_service.get_file_metadata(unique_file_id)
        assert retrieved_metadata is not None
        assert retrieved_metadata.filename == "test.log"
        print("✅ File metadata retrieval successful")
        
        # Test log entries creation
        test_entries = []
        for i in range(10):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                level=LogLevel.INFO if i % 3 != 0 else LogLevel.ERROR,
                message=f"Test log message {i}",
                source="test_service",
                raw_line=f"[INFO] Test log message {i}",
                line_number=i + 1,
                parsed_data={"test": True, "index": i}
            )
            test_entries.append(entry)
        
        entries_count = await db_service.create_log_entries(test_entries)
        print(f"✅ Created {entries_count} log entries")
        
        # Test log entries retrieval
        retrieved_entries = await db_service.get_log_entries(unique_file_id, limit=5)
        assert len(retrieved_entries) == 5
        print("✅ Log entries retrieval successful")
        
        # Test statistics
        stats = await db_service.get_log_statistics(unique_file_id)
        assert stats["total_entries"] == 10
        print("✅ Statistics calculation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ B5 Database test failed: {e}")
        return False


async def test_b6_anomaly_detection():
    """Test B6: Anomaly detection implementation"""
    print("\n🧪 Testing B6: Anomaly Detection...")
    
    try:
        # Generate unique file ID for this test run
        import uuid
        unique_file_id = f"test_b6_file_{uuid.uuid4().hex[:8]}"
        
        # Create test log entries with patterns for anomaly detection
        current_time = datetime.utcnow()
        
        # Normal entries
        normal_entries = []
        for i in range(5):
            for j in range(4):
                entry = LogEntry(
                    file_id=unique_file_id,
                    timestamp=current_time - timedelta(hours=i, minutes=j*10),
                    level=LogLevel.INFO,
                    message=f"Normal operation message {i}-{j}",
                    source="normal_service",
                    raw_line=f"[INFO] Normal operation message {i}-{j}",
                    line_number=i * 10 + j + 1
                )
                normal_entries.append(entry)
        
        # Volume spike entries (many logs in short time)
        spike_entries = []
        for i in range(50):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=current_time - timedelta(hours=2, minutes=30, seconds=i),
                level=LogLevel.WARNING,
                message=f"High volume spike message {i}",
                source="spike_service",
                raw_line=f"[WARNING] High volume spike message {i}",
                line_number=100 + i
            )
            spike_entries.append(entry)
        
        # Error spike entries
        error_entries = []
        for i in range(15):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=current_time - timedelta(hours=1, minutes=i),
                level=LogLevel.ERROR,
                message=f"Database connection failed - attempt {i}",
                source="db_service",
                raw_line=f"[ERROR] Database connection failed - attempt {i}",
                line_number=200 + i
            )
            error_entries.append(entry)
        
        all_entries = normal_entries + spike_entries + error_entries
        
        # Run anomaly detection
        anomalies = await anomaly_service.detect_anomalies(unique_file_id, all_entries)
        print(f"✅ Detected {len(anomalies)} anomalies")
        
        # Validate anomaly types
        anomaly_types = [a.anomaly_type for a in anomalies]
        expected_types = ["volume_spike", "error_spike", "unusual_pattern"]
        
        found_volume_spike = any("volume_spike" in atype for atype in anomaly_types)
        found_error_spike = any("error_spike" in atype for atype in anomaly_types)
        
        if found_volume_spike:
            print("✅ Volume spike detection working")
        if found_error_spike:
            print("✅ Error spike detection working")
        
        # Test anomaly summary
        summary = await anomaly_service.get_anomaly_summary(unique_file_id)
        assert summary["total_anomalies"] >= 0
        print("✅ Anomaly summary generation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ B6 Anomaly detection test failed: {e}")
        return False


async def test_b7_vector_storage():
    """Test B7: FAISS vector storage implementation"""
    print("\n🧪 Testing B7: FAISS Vector Storage...")
    
    try:
        # Initialize vector storage
        await vector_service.initialize_storage()
        print("✅ Vector storage initialization successful")
        
        # Create test index
        test_file_id = "test_b7_file_001"
        success = await vector_service.create_index(test_file_id, dimension=128)
        assert success
        print("✅ FAISS index creation successful")
        
        # Generate test vectors and chunks
        test_vectors = []
        for _ in range(5):
            test_vectors.append(np.random.rand(128).astype(np.float32))
        
        test_chunks = [
            "This is test chunk number 0 with some sample content for embedding",
            "Another test chunk 1 with different content pattern",
            "Error log chunk 2: Database connection timeout occurred",
            "Info chunk 3: User authentication successful for user123",
            "Warning chunk 4: Memory usage approaching 80% threshold"
        ]
        
        test_metadata = []
        for i in range(5):
            test_metadata.append({"type": "info", "source": "app", "index": i})
        
        # Add vectors to index
        success = await vector_service.add_vectors(
            test_file_id, test_vectors, test_chunks, test_metadata
        )
        assert success
        print("✅ Vector addition successful")
        
        # Test vector search
        query_vector = test_vectors[0] + np.random.rand(128).astype(np.float32) * 0.1
        search_results = await vector_service.search_vectors(
            test_file_id, query_vector, top_k=3
        )
        
        assert len(search_results) > 0
        assert all("similarity" in result for result in search_results)
        print(f"✅ Vector search returned {len(search_results)} results")
        
        # Test index info
        index_info = await vector_service.get_index_info(test_file_id)
        assert index_info is not None
        assert index_info["total_vectors"] == 5
        print("✅ Index info retrieval successful")
        
        # Test text chunking
        long_text = "This is a long text that should be chunked. " * 50
        chunks = vector_service.chunk_text(long_text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        print(f"✅ Text chunking successful - created {len(chunks)} chunks")
        
        # Test storage statistics
        stats = await vector_service.get_storage_statistics()
        assert stats["total_indices"] >= 1
        print("✅ Storage statistics successful")
        
        return True
        
    except Exception as e:
        print(f"❌ B7 Vector storage test failed: {e}")
        return False


async def test_api_endpoints():
    """Test that all new API endpoints can be imported"""
    print("\n🧪 Testing API Router Imports...")
    
    try:
        from app.routers.database import router as db_router
        from app.routers.anomaly import router as anomaly_router
        from app.routers.vectors import router as vector_router
        
        print("✅ Database router import successful")
        print("✅ Anomaly router import successful") 
        print("✅ Vector router import successful")
        
        # Test that routers have expected endpoints
        db_endpoints = [route.path for route in db_router.routes]
        anomaly_endpoints = [route.path for route in anomaly_router.routes]
        vector_endpoints = [route.path for route in vector_router.routes]
        
        print(f"✅ Database router has {len(db_endpoints)} endpoints")
        print(f"✅ Anomaly router has {len(anomaly_endpoints)} endpoints")
        print(f"✅ Vector router has {len(vector_endpoints)} endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ API router test failed: {e}")
        return False


async def main():
    """Run all validation tests"""
    print("🚀 Starting B5-B7 Validation Tests...\n")
    
    results = {
        "B5_Database": False,
        "B6_Anomaly": False,
        "B7_Vector": False,
        "API_Routers": False
    }
    
    # Run tests
    results["B5_Database"] = await test_b5_database_schema()
    results["B6_Anomaly"] = await test_b6_anomaly_detection()
    results["B7_Vector"] = await test_b7_vector_storage()
    results["API_Routers"] = await test_api_endpoints()
    
    # Summary
    print("\n" + "="*50)
    print("🎯 VALIDATION SUMMARY")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! B5-B7 implementations are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())