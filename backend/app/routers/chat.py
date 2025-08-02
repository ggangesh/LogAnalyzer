"""
Chat API Router for LogSage AI
GPT-4/4o integration for log analysis conversations
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.chat_service import chat_service, ChatMessage
from ..services.database_service import db_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    system_prompt_type: str = "log_analysis"
    model: Optional[str] = None
    temperature: Optional[float] = None


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatWithHistoryRequest(BaseModel):
    message: str
    chat_history: List[ChatHistoryMessage] = []
    use_rag: bool = True
    system_prompt_type: str = "log_analysis"


class AnalysisRequest(BaseModel):
    analysis_type: str = "summary"  # summary, errors, anomalies, security, performance, troubleshooting


class ConversationSummaryRequest(BaseModel):
    messages: List[ChatHistoryMessage]


@router.get("/status")
async def get_chat_service_status():
    """Get chat service status and configuration"""
    try:
        status = chat_service.get_service_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat service status: {str(e)}")


@router.post("/message/{file_id}")
async def send_chat_message(file_id: str, request: ChatRequest):
    """Send a chat message about logs"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Send chat message
        result = await chat_service.chat_with_logs(
            file_id=file_id,
            user_message=request.message,
            use_rag=request.use_rag,
            system_prompt_type=request.system_prompt_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat message failed: {str(e)}")


@router.post("/conversation/{file_id}")
async def chat_with_history(file_id: str, request: ChatWithHistoryRequest):
    """Continue a conversation with chat history"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert request history to ChatMessage objects
        chat_history = []
        for msg in request.chat_history:
            timestamp = None
            if msg.timestamp:
                try:
                    timestamp = datetime.fromisoformat(msg.timestamp)
                except:
                    pass
            
            chat_history.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=timestamp
            ))
        
        # Send chat message with history
        result = await chat_service.chat_with_logs(
            file_id=file_id,
            user_message=request.message,
            chat_history=chat_history,
            use_rag=request.use_rag,
            system_prompt_type=request.system_prompt_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@router.post("/analyze/{file_id}")
async def analyze_logs(file_id: str, request: AnalysisRequest):
    """Perform AI analysis of logs"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform analysis
        result = await chat_service.analyze_logs_with_ai(
            file_id=file_id,
            analysis_type=request.analysis_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Log analysis failed: {str(e)}")


@router.post("/summary")
async def summarize_conversation(request: ConversationSummaryRequest):
    """Generate a summary of a conversation"""
    try:
        # Convert request messages to ChatMessage objects
        messages = []
        for msg in request.messages:
            timestamp = None
            if msg.timestamp:
                try:
                    timestamp = datetime.fromisoformat(msg.timestamp)
                except:
                    pass
            
            messages.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=timestamp
            ))
        
        # Generate summary
        summary = await chat_service.get_conversation_summary(messages)
        
        return {
            "summary": summary,
            "message_count": len(messages),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation summary failed: {str(e)}")


@router.get("/models")
async def get_available_models():
    """Get information about available chat models"""
    return {
        "primary_model": chat_service.model,
        "fallback_model": chat_service.fallback_model,
        "available_models": [
            {
                "name": "gpt-4o-mini",
                "description": "Fast, cost-effective model for most tasks",
                "max_tokens": 128000,
                "recommended_use": "General chat and analysis"
            },
            {
                "name": "gpt-4o",
                "description": "Most capable model for complex analysis",
                "max_tokens": 128000,
                "recommended_use": "Complex troubleshooting and detailed analysis"
            },
            {
                "name": "gpt-4-turbo",
                "description": "Balanced model for comprehensive analysis",
                "max_tokens": 128000,
                "recommended_use": "Detailed log analysis and insights"
            },
            {
                "name": "gpt-3.5-turbo",
                "description": "Fallback model for basic interactions",
                "max_tokens": 16385,
                "recommended_use": "Simple queries and summaries"
            }
        ],
        "current_configuration": {
            "max_tokens": chat_service.max_tokens,
            "temperature": chat_service.temperature,
            "api_key_configured": bool(chat_service.api_key)
        }
    }


@router.get("/prompts")
async def get_system_prompts():
    """Get available system prompt types"""
    return {
        "available_prompts": list(chat_service.system_prompts.keys()),
        "descriptions": {
            "log_analysis": "Expert log analysis with technical insights and troubleshooting",
            "general": "General-purpose assistant for log-related questions",
            "troubleshooting": "Focused on diagnosing and solving system issues"
        },
        "default_prompt": "log_analysis"
    }


@router.get("/analysis-types")
async def get_analysis_types():
    """Get available analysis types"""
    return {
        "analysis_types": [
            {
                "type": "summary",
                "description": "Comprehensive overview of log data with key insights"
            },
            {
                "type": "errors",
                "description": "Analysis of error patterns and their potential causes"
            },
            {
                "type": "anomalies",
                "description": "Review of detected anomalies and unusual patterns"
            },
            {
                "type": "security",
                "description": "Security-focused analysis for threats and suspicious activities"
            },
            {
                "type": "performance",
                "description": "Performance analysis identifying bottlenecks and issues"
            },
            {
                "type": "troubleshooting",
                "description": "Actionable troubleshooting recommendations and next steps"
            }
        ],
        "default_type": "summary"
    }


@router.post("/quick-ask/{file_id}")
async def quick_ask(file_id: str, question: str):
    """Quick ask interface for simple questions"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Use simple chat with RAG
        result = await chat_service.chat_with_logs(
            file_id=file_id,
            user_message=question,
            use_rag=True,
            system_prompt_type="general"
        )
        
        return {
            "question": question,
            "answer": result["assistant_response"],
            "model": result["model_used"],
            "response_time": result["response_time"],
            "file_id": file_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick ask failed: {str(e)}")


@router.get("/demo/{file_id}")
async def chat_demo(file_id: str, message: str = "What are the main issues in these logs?"):
    """Demo endpoint to showcase chat capabilities"""
    try:
        # Check if file exists
        metadata = await db_service.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform demo chat
        result = await chat_service.chat_with_logs(
            file_id=file_id,
            user_message=message,
            use_rag=True,
            system_prompt_type="log_analysis"
        )
        
        # Format for demo presentation
        demo_result = {
            "demo_message": message,
            "file_id": file_id,
            "filename": metadata.filename,
            "chat_features": {
                "rag_enabled": result.get("rag_enabled", False),
                "context_used": result.get("context_used", False),
                "model_used": result.get("model_used", "unknown"),
                "response_time": result.get("response_time", 0)
            },
            "ai_response": result["assistant_response"],
            "context_stats": result.get("rag_stats", {}),
            "capabilities_demonstrated": [
                "Natural language query processing",
                "RAG-enhanced context retrieval",
                "Log-specific AI analysis",
                "Conversational interface"
            ]
        }
        
        return demo_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat demo failed: {str(e)}")


@router.get("/health")
async def chat_health_check():
    """Health check for chat service"""
    try:
        # Test basic functionality
        status = chat_service.get_service_status()
        
        return {
            "service": "Chat Service",
            "status": "healthy",
            "configuration": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "service": "Chat Service",
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }