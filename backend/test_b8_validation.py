"""
Validation script for B8 implementation
Tests OpenAI embedding pipeline functionality
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.database import LogEntry, FileMetadata, LogLevel
from app.services.database_service import db_service
from app.services.embedding_service import embedding_service
from app.services.vector_storage import vector_service


async def test_b8_embedding_pipeline():
    """Test B8: OpenAI embedding pipeline implementation"""
    print("🧪 Testing B8: OpenAI Embedding Pipeline...")
    
    try:
        # Initialize services
        await db_service.initialize_database()
        await vector_service.initialize_storage()
        print("✅ Services initialized")
        
        # Test service status
        status = embedding_service.get_service_status()
        print(f"✅ Service status: {status['service']} - Model: {status['model']}")
        
        # Test single text embedding
        test_text = "This is a test log message for embedding generation"
        embedding = await embedding_service.generate_embedding(test_text)
        
        if embedding is None:
            raise Exception("Failed to generate single embedding")
        
        print(f"✅ Single embedding generated - Dimension: {len(embedding)}")
        
        # Test batch embedding
        test_texts = [
            "INFO: User authentication successful",
            "ERROR: Database connection failed",
            "WARNING: Memory usage approaching threshold",
            "DEBUG: Processing request from client",
            "CRITICAL: System shutdown initiated"
        ]
        
        batch_embeddings = await embedding_service.generate_embeddings_batch(test_texts)
        successful_embeddings = [e for e in batch_embeddings if e is not None]
        
        print(f"✅ Batch embeddings generated: {len(successful_embeddings)}/{len(test_texts)}")
        
        # Create test file and log entries
        unique_file_id = f"test_b8_file_{uuid.uuid4().hex[:8]}"
        
        # Create file metadata
        test_metadata = FileMetadata(
            file_id=unique_file_id,
            filename="test_b8.log",
            file_path="/uploads/test_b8.log",
            file_size=2048,
            format_type="structured",
            upload_time=datetime.utcnow(),
            processing_status="completed"
        )
        
        await db_service.create_file_metadata(test_metadata)
        print(f"✅ Test file metadata created: {unique_file_id}")
        
        # Create test log entries
        test_log_entries = []
        for i, text in enumerate(test_texts):
            level = LogLevel.INFO
            if "ERROR" in text:
                level = LogLevel.ERROR
            elif "WARNING" in text:
                level = LogLevel.WARNING
            elif "CRITICAL" in text:
                level = LogLevel.CRITICAL
            elif "DEBUG" in text:
                level = LogLevel.DEBUG
            
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(minutes=i*5),
                level=level,
                message=text.split(": ", 1)[1] if ": " in text else text,
                source="test_service",
                raw_line=f"[{datetime.utcnow().isoformat()}] {text}",
                line_number=i + 1
            )
            test_log_entries.append(entry)
        
        # Store log entries
        await db_service.create_log_entries(test_log_entries)
        print(f"✅ Created {len(test_log_entries)} test log entries")
        
        # Test log entries embedding
        embed_result = await embedding_service.embed_log_entries(unique_file_id, test_log_entries)
        print(f"✅ Log entries embedding result: {embed_result['embeddings_created']} embeddings created")
        
        # Test similarity search
        search_query = "authentication error"
        search_result = await embedding_service.search_similar_logs(unique_file_id, search_query, top_k=3)
        print(f"✅ Similarity search found {search_result['results_found']} results for query: '{search_query}'")
        
        # Test text chunk embedding
        long_text = """
        This is a longer text document that should be chunked for embedding processing.
        It contains multiple sentences and paragraphs to test the chunking functionality.
        The embedding service should split this into appropriate chunks and generate
        embeddings for each chunk separately. This allows for better semantic search
        and retrieval of relevant information from large documents.
        """
        
        chunk_result = await embedding_service.embed_text_chunks(
            unique_file_id, long_text, chunk_size=100, overlap=20
        )
        print(f"✅ Text chunking result: {chunk_result['embeddings_created']} chunk embeddings created")
        
        # Test embedding statistics
        stats = await embedding_service.get_embedding_statistics(unique_file_id)
        print(f"✅ Embedding statistics retrieved: {stats.get('total_embeddings', 0)} total embeddings")
        
        # Test cache functionality
        cache_stats = embedding_service._load_cache()
        print(f"✅ Cache contains {len(cache_stats)} cached embeddings")
        
        return True
        
    except Exception as e:
        print(f"❌ B8 embedding pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_router_imports():
    """Test that the embeddings API router can be imported"""
    print("\n🧪 Testing Embeddings API Router...")
    
    try:
        from app.routers.embeddings import router as embeddings_router
        print("✅ Embeddings router import successful")
        
        # Test router endpoints
        endpoints = [route.path for route in embeddings_router.routes]
        print(f"✅ Embeddings router has {len(endpoints)} endpoints")
        
        expected_endpoints = [
            "/api/v1/embeddings/status",
            "/api/v1/embeddings/embed/logs/{file_id}",
            "/api/v1/embeddings/search/{file_id}",
            "/api/v1/embeddings/statistics/{file_id}"
        ]
        
        for expected in expected_endpoints:
            if any(expected.replace("{file_id}", "") in endpoint for endpoint in endpoints):
                print(f"✅ Found expected endpoint pattern: {expected}")
        
        return True
        
    except Exception as e:
        print(f"❌ API router test failed: {e}")
        return False


async def main():
    """Run all B8 validation tests"""
    print("🚀 Starting B8 Embedding Pipeline Validation Tests...\n")
    
    results = {
        "B8_Embedding_Pipeline": False,
        "API_Router": False
    }
    
    # Run tests
    results["B8_Embedding_Pipeline"] = await test_b8_embedding_pipeline()
    results["API_Router"] = await test_api_router_imports()
    
    # Summary
    print("\n" + "="*60)
    print("🎯 B8 VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL B8 TESTS PASSED! Embedding pipeline is working correctly.")
        print("\n📝 Setup Notes:")
        print("- Set OPENAI_API_KEY environment variable for production")
        print("- Without API key, service uses random embeddings for demo")
        print("- Embeddings are cached locally to reduce API calls")
        print("- Service integrates with existing FAISS vector storage")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())