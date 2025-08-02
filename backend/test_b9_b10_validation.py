"""
Validation script for B9-B10 implementations
Tests RAG pipeline and GPT-4/4o chat integration
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
from app.services.rag_service import rag_service
from app.services.chat_service import chat_service, ChatMessage


async def test_b9_rag_pipeline():
    """Test B9: RAG pipeline implementation"""
    print("🧪 Testing B9: RAG Pipeline...")
    
    try:
        # Initialize services
        await db_service.initialize_database()
        await vector_service.initialize_storage()
        print("✅ Services initialized")
        
        # Create test file and data
        unique_file_id = f"test_b9_file_{uuid.uuid4().hex[:8]}"
        
        # Create file metadata
        test_metadata = FileMetadata(
            file_id=unique_file_id,
            filename="test_b9_rag.log",
            file_path="/uploads/test_b9_rag.log",
            file_size=4096,
            format_type="structured",
            upload_time=datetime.utcnow(),
            processing_status="completed"
        )
        
        await db_service.create_file_metadata(test_metadata)
        print(f"✅ Test file metadata created: {unique_file_id}")
        
        # Create diverse test log entries
        test_log_entries = [
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=2),
                level=LogLevel.ERROR,
                message="Database connection timeout after 30 seconds",
                source="db_service",
                raw_line="[ERROR] Database connection timeout after 30 seconds",
                line_number=1
            ),
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=30),
                level=LogLevel.WARNING,
                message="Memory usage at 85% - approaching threshold",
                source="monitor_service",
                raw_line="[WARNING] Memory usage at 85% - approaching threshold", 
                line_number=2
            ),
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=1),
                level=LogLevel.INFO,
                message="User authentication successful for user john.doe",
                source="auth_service",
                raw_line="[INFO] User authentication successful for user john.doe",
                line_number=3
            ),
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(minutes=30),
                level=LogLevel.CRITICAL,
                message="System disk space critically low - only 2% remaining",
                source="system_monitor",
                raw_line="[CRITICAL] System disk space critically low - only 2% remaining",
                line_number=4
            ),
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(minutes=10),
                level=LogLevel.ERROR,
                message="Failed to process payment for order #12345",
                source="payment_service",
                raw_line="[ERROR] Failed to process payment for order #12345",
                line_number=5
            )
        ]
        
        # Store log entries
        await db_service.create_log_entries(test_log_entries)
        print(f"✅ Created {len(test_log_entries)} test log entries")
        
        # Generate embeddings for log entries
        embed_result = await embedding_service.embed_log_entries(unique_file_id, test_log_entries)
        print(f"✅ Generated embeddings: {embed_result['embeddings_created']} created")
        
        # Test RAG retrieval
        test_query = "What database issues occurred?"
        retrieved_chunks = await rag_service.retrieve_relevant_chunks(unique_file_id, test_query, top_k=3)
        print(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks for query: '{test_query}'")
        
        # Test context preparation
        rag_context = await rag_service.prepare_rag_context(test_query, retrieved_chunks)
        print(f"✅ Prepared RAG context: {len(rag_context.context_text)} characters")
        
        # Test complete RAG pipeline
        full_context = await rag_service.retrieve_log_context(unique_file_id, test_query)
        print(f"✅ Complete RAG pipeline: {full_context.get('retrieval_stats', {}).get('chunks_retrieved', 0)} chunks retrieved")
        
        # Test document chunking
        test_document = """
        This is a test document for RAG processing. It contains multiple sentences
        and paragraphs to test the chunking functionality. The system should be able
        to split this into appropriate chunks and generate embeddings for similarity search.
        This enables semantic search and retrieval of relevant information.
        """
        
        chunk_result = await rag_service.chunk_and_embed_document(unique_file_id, test_document)
        print(f"✅ Document chunking: {chunk_result['embeddings_created']} chunk embeddings created")
        
        # Test RAG statistics
        rag_stats = await rag_service.get_rag_statistics(unique_file_id)
        print(f"✅ RAG statistics retrieved successfully")
        
        # Test RAG configuration
        config = rag_service.update_rag_config(max_chunks=5, similarity_threshold=0.2)
        print(f"✅ RAG configuration updated: max_chunks={config['max_chunks']}")
        
        return True
        
    except Exception as e:
        print(f"❌ B9 RAG pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_b10_chat_integration():
    """Test B10: GPT-4/4o chat integration"""
    print("\n🧪 Testing B10: GPT-4/4o Chat Integration...")
    
    try:
        # Test service status
        status = chat_service.get_service_status()
        print(f"✅ Chat service status: {status['service']} - Model: {status['primary_model']}")
        
        # Create a test file for chat context
        unique_file_id = f"test_b10_file_{uuid.uuid4().hex[:8]}"
        
        # Create file metadata
        test_metadata = FileMetadata(
            file_id=unique_file_id,
            filename="test_b10_chat.log",
            file_path="/uploads/test_b10_chat.log",
            file_size=2048,
            format_type="structured",
            upload_time=datetime.utcnow(),
            processing_status="completed"
        )
        
        await db_service.create_file_metadata(test_metadata)
        print(f"✅ Test file metadata created: {unique_file_id}")
        
        # Create test log entries for chat context
        chat_test_entries = [
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(hours=1),
                level=LogLevel.ERROR,
                message="Connection refused by database server",
                source="web_app",
                raw_line="[ERROR] Connection refused by database server",
                line_number=1
            ),
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow() - timedelta(minutes=30),
                level=LogLevel.WARNING,
                message="High CPU usage detected: 92%",
                source="monitoring",
                raw_line="[WARNING] High CPU usage detected: 92%",
                line_number=2
            )
        ]
        
        await db_service.create_log_entries(chat_test_entries)
        await embedding_service.embed_log_entries(unique_file_id, chat_test_entries)
        print(f"✅ Created test data for chat context")
        
        # Test basic chat completion
        test_messages = [
            ChatMessage(role="user", content="Hello, can you help me analyze these logs?")
        ]
        
        response = await chat_service.generate_chat_completion(test_messages)
        print(f"✅ Basic chat completion: {len(response.message)} characters response")
        
        # Test chat with logs (RAG integration) 
        chat_result = await chat_service.chat_with_logs(
            file_id=unique_file_id,
            user_message="What errors are occurring in the system?",
            use_rag=True
        )
        print(f"✅ Chat with logs: Response generated using model {chat_result.get('model_used', 'unknown')}")
        
        # Test chat with history
        chat_history = [
            ChatMessage(role="user", content="What's the status of the system?"),
            ChatMessage(role="assistant", content="The system shows some issues that need attention.")
        ]
        
        history_result = await chat_service.chat_with_logs(
            file_id=unique_file_id,
            user_message="What specific issues should I address first?",
            chat_history=chat_history,
            use_rag=True
        )
        print(f"✅ Chat with history: Context-aware response generated")
        
        # Test log analysis
        analysis_result = await chat_service.analyze_logs_with_ai(
            file_id=unique_file_id,
            analysis_type="summary"
        )
        print(f"✅ AI log analysis: {analysis_result['analysis_type']} completed")
        
        # Test conversation summary
        conversation_messages = [
            ChatMessage(role="user", content="What errors are in the logs?"),
            ChatMessage(role="assistant", content="I found database connection errors and high CPU usage warnings."),
            ChatMessage(role="user", content="How should I fix these?"),
            ChatMessage(role="assistant", content="Check database connectivity and investigate high CPU processes.")
        ]
        
        summary = await chat_service.get_conversation_summary(conversation_messages)
        print(f"✅ Conversation summary: {len(summary)} characters generated")
        
        return True
        
    except Exception as e:
        print(f"❌ B10 chat integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_router_imports():
    """Test that both RAG and Chat API routers can be imported"""
    print("\n🧪 Testing RAG and Chat API Routers...")
    
    try:
        from app.routers.rag import router as rag_router
        from app.routers.chat import router as chat_router
        
        print("✅ RAG router import successful")
        print("✅ Chat router import successful")
        
        # Test router endpoints
        rag_endpoints = [route.path for route in rag_router.routes]
        chat_endpoints = [route.path for route in chat_router.routes]
        
        print(f"✅ RAG router has {len(rag_endpoints)} endpoints")
        print(f"✅ Chat router has {len(chat_endpoints)} endpoints")
        
        # Check for expected endpoints
        expected_rag_endpoints = [
            "/api/v1/rag/status",
            "/api/v1/rag/query/{file_id}",
            "/api/v1/rag/retrieve/{file_id}",
            "/api/v1/rag/statistics/{file_id}"
        ]
        
        expected_chat_endpoints = [
            "/api/v1/chat/status", 
            "/api/v1/chat/message/{file_id}",
            "/api/v1/chat/analyze/{file_id}",
            "/api/v1/chat/models"
        ]
        
        for expected in expected_rag_endpoints:
            if any(expected.replace("{file_id}", "") in endpoint for endpoint in rag_endpoints):
                print(f"✅ Found expected RAG endpoint pattern: {expected}")
        
        for expected in expected_chat_endpoints:
            if any(expected.replace("{file_id}", "") in endpoint for endpoint in chat_endpoints):
                print(f"✅ Found expected Chat endpoint pattern: {expected}")
        
        return True
        
    except Exception as e:
        print(f"❌ API router test failed: {e}")
        return False


async def test_integration():
    """Test integration between RAG and Chat services"""
    print("\n🧪 Testing B9-B10 Integration...")
    
    try:
        # Create integration test file
        unique_file_id = f"test_integration_{uuid.uuid4().hex[:8]}"
        
        test_metadata = FileMetadata(
            file_id=unique_file_id,
            filename="integration_test.log",
            file_path="/uploads/integration_test.log",
            file_size=1024,
            format_type="structured",
            upload_time=datetime.utcnow(),
            processing_status="completed"
        )
        
        await db_service.create_file_metadata(test_metadata)
        
        # Create test entries
        integration_entries = [
            LogEntry(
                file_id=unique_file_id,
                timestamp=datetime.utcnow(),
                level=LogLevel.ERROR,
                message="Integration test error message",
                source="test_service",
                raw_line="[ERROR] Integration test error message",
                line_number=1
            )
        ]
        
        await db_service.create_log_entries(integration_entries)
        await embedding_service.embed_log_entries(unique_file_id, integration_entries)
        
        # Test RAG -> Chat pipeline
        rag_context = await rag_service.retrieve_and_prepare_context(
            unique_file_id, "What integration test errors occurred?"
        )
        
        chat_response = await chat_service.generate_chat_completion(
            [ChatMessage(role="user", content="Analyze this log context")],
            context=rag_context.context_text
        )
        
        print(f"✅ RAG->Chat integration: Context ({len(rag_context.context_text)} chars) -> Response ({len(chat_response.message)} chars)")
        
        # Test complete pipeline
        full_result = await chat_service.chat_with_logs(
            unique_file_id, 
            "What can you tell me about this integration test?",
            use_rag=True
        )
        
        print(f"✅ Complete pipeline: RAG-enhanced chat response generated")
        print(f"   - RAG enabled: {full_result.get('rag_enabled', False)}")
        print(f"   - Context used: {full_result.get('context_used', False)}")
        print(f"   - Response time: {full_result.get('response_time', 0):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all B9-B10 validation tests"""
    print("🚀 Starting B9-B10 Validation Tests...\n")
    
    results = {
        "B9_RAG_Pipeline": False,
        "B10_Chat_Integration": False,
        "API_Routers": False,
        "Integration": False
    }
    
    # Run tests
    results["B9_RAG_Pipeline"] = await test_b9_rag_pipeline()
    results["B10_Chat_Integration"] = await test_b10_chat_integration()
    results["API_Routers"] = await test_api_router_imports()
    results["Integration"] = await test_integration()
    
    # Summary
    print("\n" + "="*60)
    print("🎯 B9-B10 VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL B9-B10 TESTS PASSED! RAG pipeline and Chat integration working correctly.")
        print("\n📝 Setup Notes:")
        print("- Set OPENAI_API_KEY environment variable for production")
        print("- Without API key, services use demo mode with mock responses")  
        print("- RAG pipeline integrates with existing embedding and vector storage")
        print("- Chat service supports conversation history and multiple analysis types")
        print("- Full pipeline: Upload -> Parse -> Embed -> RAG -> Chat")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())