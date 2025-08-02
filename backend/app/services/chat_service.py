"""
GPT-4/4o Chat Service for LogSage AI
Basic API calls and simple error handling for MVP
"""
import openai
import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import os
from dataclasses import dataclass

from .rag_service import rag_service, RAGContext


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class ChatResponse:
    """Represents a chat completion response"""
    message: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    context_used: bool = False
    context_length: int = 0


class ChatService:
    """Service for GPT-4/4o chat completions with RAG integration"""
    
    def __init__(self):
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"  # Start with mini for demo, can upgrade to gpt-4o
        self.fallback_model = "gpt-3.5-turbo"  # Fallback if gpt-4o not available
        self.max_tokens = 2000  # Max response tokens
        self.temperature = 0.1  # Low temperature for factual responses
        
        # Initialize OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
        
        # System prompts for different use cases
        self.system_prompts = {
            "log_analysis": """You are LogSage AI, an expert log analysis assistant. You help users understand their log data, identify issues, and provide actionable insights.

Your capabilities:
- Analyze log patterns and anomalies
- Explain error messages and their causes
- Suggest troubleshooting steps
- Identify security concerns
- Provide system health insights

When responding:
- Be concise but thorough
- Use technical language appropriately
- Provide specific examples from the log data when available
- Suggest concrete next steps
- If you're uncertain about something, say so clearly""",

            "general": """You are LogSage AI, a helpful assistant for log analysis and system monitoring. You provide clear, accurate information about log data and system behavior.

Be helpful, accurate, and concise in your responses.""",

            "troubleshooting": """You are LogSage AI, a troubleshooting expert. You help diagnose system issues based on log data and provide step-by-step solutions.

Focus on:
- Identifying root causes
- Providing clear diagnostic steps
- Suggesting specific solutions
- Prioritizing critical issues"""
        }
    
    async def generate_chat_completion(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        context: Optional[str] = None
    ) -> ChatResponse:
        """Generate a chat completion using OpenAI API"""
        start_time = datetime.utcnow()
        
        if not self.api_key:
            # Demo mode - return a mock response
            return self._generate_demo_response(messages, context)
        
        try:
            # Use provided parameters or defaults
            model = model or self.model
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            
            # Prepare messages for OpenAI API
            api_messages = []
            for msg in messages:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add context if provided
            context_length = 0
            if context:
                context_length = len(context)
                # Insert context before the last user message
                if api_messages and api_messages[-1]["role"] == "user":
                    user_message = api_messages[-1]["content"]
                    api_messages[-1]["content"] = f"Context information:\n{context}\n\nUser question: {user_message}"
                else:
                    api_messages.append({
                        "role": "user",
                        "content": f"Context: {context}"
                    })
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract response data
            message_content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return ChatResponse(
                message=message_content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                response_time=response_time,
                context_used=bool(context),
                context_length=context_length
            )
            
        except Exception as e:
            print(f"Error in chat completion: {e}")
            
            # Try fallback model if main model fails
            if model != self.fallback_model:
                try:
                    return await self.generate_chat_completion(
                        messages, 
                        model=self.fallback_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        context=context
                    )
                except Exception as fallback_error:
                    print(f"Fallback model also failed: {fallback_error}")
            
            # Return error response
            response_time = (datetime.utcnow() - start_time).total_seconds()
            return ChatResponse(
                message=f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}",
                model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                finish_reason="error",
                response_time=response_time,
                context_used=bool(context),
                context_length=len(context) if context else 0
            )
    
    def _generate_demo_response(self, messages: List[ChatMessage], context: Optional[str] = None) -> ChatResponse:
        """Generate a demo response when API key is not available"""
        user_message = ""
        for msg in messages:
            if msg.role == "user":
                user_message = msg.content.lower()
                break
        
        # Simple keyword-based responses for demo
        demo_responses = {
            "error": "Based on the log data, I can see there are error patterns that need attention. Common causes include network connectivity issues, configuration problems, or resource constraints. I'd recommend checking system resources and configuration files.",
            
            "anomaly": "I've detected some anomalies in your log patterns. These could indicate unusual system behavior or potential issues. The anomalies include volume spikes and error rate increases that warrant investigation.",
            
            "summary": "Here's a summary of your log data: The system shows normal operation with some intermittent issues. Key findings include periodic error spikes and some unusual patterns that may need monitoring.",
            
            "help": "I'm LogSage AI, your log analysis assistant. I can help you understand log patterns, identify issues, troubleshoot problems, and provide insights about your system's behavior. What would you like to know about your logs?",
            
            "default": "I understand you're asking about your log data. While I'm currently in demo mode (no OpenAI API key configured), I can help analyze patterns, identify issues, and provide insights based on the log information available."
        }
        
        # Choose response based on keywords
        response_text = demo_responses["default"]
        for keyword, response in demo_responses.items():
            if keyword in user_message:
                response_text = response
                break
        
        if context:
            response_text += f"\n\nBased on the context provided ({len(context)} characters), I can see relevant log information that supports this analysis."
        
        return ChatResponse(
            message=response_text,
            model="demo-mode",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="demo",
            response_time=0.1,
            context_used=bool(context),
            context_length=len(context) if context else 0
        )
    
    async def chat_with_logs(
        self, 
        file_id: str, 
        user_message: str,
        chat_history: List[ChatMessage] = None,
        use_rag: bool = True,
        system_prompt_type: str = "log_analysis"
    ) -> Dict[str, Any]:
        """Chat about logs with RAG context"""
        try:
            # Prepare chat history
            if chat_history is None:
                chat_history = []
            
            # Add system prompt
            messages = [ChatMessage(
                role="system", 
                content=self.system_prompts.get(system_prompt_type, self.system_prompts["general"])
            )]
            
            # Add chat history
            messages.extend(chat_history)
            
            # Get RAG context if requested
            context = None
            rag_stats = None
            
            if use_rag:
                try:
                    rag_result = await rag_service.query_logs_with_rag(file_id, user_message)
                    if "rag_context" in rag_result and hasattr(rag_result["rag_context"], "context_text"):
                        context = rag_result["rag_context"].context_text
                        rag_stats = rag_result.get("retrieval_stats", {})
                    elif "context" in rag_result:
                        context = rag_result["context"]
                    
                    # Also include anomalies and errors if available
                    if "additional_context" in rag_result:
                        additional_info = []
                        if rag_result["additional_context"].get("anomalies"):
                            additional_info.append("Recent Anomalies:\n" + "\n".join(rag_result["additional_context"]["anomalies"]))
                        if rag_result["additional_context"].get("recent_errors"):
                            additional_info.append("Recent Errors:\n" + "\n".join(rag_result["additional_context"]["recent_errors"][:5]))
                        
                        if additional_info:
                            context = (context or "") + "\n\n" + "\n\n".join(additional_info)
                
                except Exception as e:
                    print(f"Error getting RAG context: {e}")
                    rag_stats = {"error": str(e)}
            
            # Add user message
            messages.append(ChatMessage(role="user", content=user_message))
            
            # Generate response
            response = await self.generate_chat_completion(messages, context=context)
            
            return {
                "user_message": user_message,
                "assistant_response": response.message,
                "model_used": response.model,
                "response_time": response.response_time,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
                "context_used": response.context_used,
                "context_length": response.context_length,
                "rag_enabled": use_rag,
                "rag_stats": rag_stats,
                "file_id": file_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in chat_with_logs: {e}")
            return {
                "user_message": user_message,
                "assistant_response": f"I apologize, but I encountered an error: {str(e)}",
                "error": str(e),
                "file_id": file_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def analyze_logs_with_ai(
        self, 
        file_id: str, 
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """Perform AI analysis of logs"""
        try:
            # Define analysis prompts
            analysis_prompts = {
                "summary": "Please provide a comprehensive summary of the log data, highlighting key patterns, issues, and insights.",
                "errors": "Analyze the error patterns in the logs. What are the most common errors and their potential causes?",
                "anomalies": "Review the detected anomalies and unusual patterns. What might be causing these anomalies?",
                "security": "Analyze the logs for potential security concerns or suspicious activities.",
                "performance": "Examine the logs for performance-related issues and bottlenecks.",
                "troubleshooting": "Based on the log data, what are the top issues that need immediate attention and how should they be addressed?"
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["summary"])
            
            # Get comprehensive RAG context
            rag_result = await rag_service.retrieve_log_context(
                file_id, prompt, include_anomalies=True, include_errors=True
            )
            
            # Prepare analysis message
            analysis_message = ChatMessage(role="user", content=prompt)
            
            # Get context from RAG
            context = None
            if "rag_context" in rag_result:
                context = rag_result["rag_context"].context_text
                
                # Add additional context
                if "additional_context" in rag_result:
                    additional_parts = []
                    if rag_result["additional_context"].get("anomalies"):
                        additional_parts.append("Detected Anomalies:\n" + "\n".join(rag_result["additional_context"]["anomalies"]))
                    if rag_result["additional_context"].get("recent_errors"):
                        additional_parts.append("Recent Errors:\n" + "\n".join(rag_result["additional_context"]["recent_errors"]))
                    
                    if additional_parts:
                        context += "\n\n" + "\n\n".join(additional_parts)
            
            # Generate analysis
            response = await self.generate_chat_completion(
                [
                    ChatMessage(role="system", content=self.system_prompts["log_analysis"]),
                    analysis_message
                ],
                context=context
            )
            
            return {
                "analysis_type": analysis_type,
                "analysis_result": response.message,
                "model_used": response.model,
                "response_time": response.response_time,
                "usage": response.usage,
                "context_length": response.context_length,
                "rag_stats": rag_result.get("retrieval_stats", {}),
                "file_id": file_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in analyze_logs_with_ai: {e}")
            return {
                "analysis_type": analysis_type,
                "error": str(e),
                "file_id": file_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get chat service status and configuration"""
        return {
            "service": "GPT-4/4o Chat Service",
            "primary_model": self.model,
            "fallback_model": self.fallback_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key),
            "available_prompts": list(self.system_prompts.keys()),
            "supported_analysis_types": [
                "summary", "errors", "anomalies", "security", 
                "performance", "troubleshooting"
            ]
        }
    
    async def get_conversation_summary(
        self, 
        messages: List[ChatMessage]
    ) -> str:
        """Generate a summary of a conversation"""
        if not messages:
            return "No conversation to summarize."
        
        try:
            # Prepare messages for summarization
            conversation_text = "\n".join([
                f"{msg.role.title()}: {msg.content}"
                for msg in messages if msg.role != "system"
            ])
            
            summary_prompt = ChatMessage(
                role="user",
                content=f"Please provide a brief summary of this conversation:\n\n{conversation_text}"
            )
            
            response = await self.generate_chat_completion([
                ChatMessage(role="system", content="You are a helpful assistant that summarizes conversations concisely."),
                summary_prompt
            ])
            
            return response.message
            
        except Exception as e:
            print(f"Error generating conversation summary: {e}")
            return f"Error generating summary: {str(e)}"


# Global chat service instance
chat_service = ChatService()