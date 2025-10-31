"""
Generator Manager - จัดการ Pre-trained LLM สำหรับสร้างคำตอบ
ตาม RAG Architecture: Query + Context → Pre-trained LLM → Response
"""
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
from datetime import datetime

from backend.components.retriever.manager import retriever_manager, RetrievalResult
from config.api_services import api_manager
from config.environment import env_center

@dataclass
class GenerationRequest:
    """คำขอสำหรับสร้างคำตอบ"""
    query: str
    context: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    model_preference: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@dataclass
class GenerationResponse:
    """ผลลัพธ์การสร้างคำตอบ"""
    answer: str
    sources: List[RetrievalResult]
    model_used: str
    context_used: str
    processing_time: float
    metadata: Dict[str, Any]

class GeneratorManager:
    """จัดการการสร้างคำตอบด้วย LLM"""
    
    def __init__(self):
        self.available_models = self._get_available_models()
        self.default_system_prompt = self._get_default_system_prompt()
    
    def _get_available_models(self) -> Dict[str, str]:
        """รายการ model ที่ใช้งานได้"""
        models = {}
        
        if api_manager.get_service("openai"):
            models.update({
                "gpt-3.5-turbo": "openai",
                "gpt-4": "openai",
                "gpt-4-turbo": "openai"
            })
        
        if api_manager.get_service("anthropic"):
            models.update({
                "claude-3-haiku": "anthropic",
                "claude-3-sonnet": "anthropic",
                "claude-3-opus": "anthropic"
            })
        
        if api_manager.get_service("google"):
            models.update({
                "gemini-pro": "google"
            })
        
        return models
    
    def _get_default_system_prompt(self) -> str:
        """System prompt เริ่มต้น"""
        return """คุณเป็น AI Assistant ที่ช่วยตอบคำถามจากเอกสารในองค์กร

หน้าที่ของคุณ:
1. ตอบคำถามโดยอิงจากข้อมูลใน context ที่ให้มา
2. หากไม่มีข้อมูลใน context ให้บอกว่าไม่พบข้อมูลที่เกี่ยวข้อง
3. อ้างอิงแหล่งที่มาของข้อมูลเมื่อเป็นไปได้
4. ตอบเป็นภาษาไทยหรือภาษาอังกฤษตามภาษาของคำถาม
5. ให้คำตอบที่ถูกต้อง เป็นประโยชน์ และครอบคลุม

หลักเกณฑ์:
- ใช้ข้อมูลจาก context เป็นหลัก
- หากข้อมูลไม่ชัดเจน ให้บอกข้อจำกัดนั้น
- ไม่แต่งหรือสร้างข้อมูลเพิ่มเติม
- ระบุแหล่งที่มาเมื่อเป็นไปได้"""
    
    async def generate_answer(self, request: GenerationRequest) -> GenerationResponse:
        """
        สร้างคำตอบจาก query และ context
        
        Args:
            request: GenerationRequest object
            
        Returns:
            GenerationResponse object
        """
        start_time = datetime.now()
        
        try:
            # 1. Get context if not provided
            context = request.context
            sources = []
            
            if not context:
                sources = await retriever_manager.search_similar(request.query, top_k=5)
                context = await retriever_manager.get_context_for_query(request.query)
            
            # 2. Select model and service
            model_name = request.model_preference or self._select_best_model()
            service_name = self.available_models.get(model_name)
            
            if not service_name:
                raise ValueError(f"Model {model_name} not available")
            
            service = api_manager.get_service(service_name)
            if not service:
                raise ValueError(f"Service {service_name} not available")
            
            # 3. Prepare messages
            messages = self._prepare_messages(request.query, context, request.conversation_history)
            
            # 4. Generate response
            if service_name == "openai":
                response = await service.chat_completion(
                    messages=messages,
                    model=model_name
                )
            elif service_name == "anthropic":
                # Convert to Anthropic format
                anthropic_messages = self._convert_to_anthropic_format(messages)
                response = await service.chat_completion(
                    messages=anthropic_messages,
                    model=self._map_to_anthropic_model(model_name)
                )
            else:
                raise ValueError(f"Service {service_name} not implemented")
            
            if not response.success:
                raise ValueError(f"Generation failed: {response.error}")
            
            # 5. Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 6. Create response
            return GenerationResponse(
                answer=response.data,
                sources=sources,
                model_used=model_name,
                context_used=context,
                processing_time=processing_time,
                metadata={
                    "query_length": len(request.query),
                    "context_length": len(context) if context else 0,
                    "sources_count": len(sources),
                    "service_used": service_name
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return GenerationResponse(
                answer=f"เกิดข้อผิดพลาดในการสร้างคำตอบ: {str(e)}",
                sources=[],
                model_used="error",
                context_used="",
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def _select_best_model(self) -> str:
        """เลือก model ที่ดีที่สุดที่มี"""
        # Priority order
        preferred_models = [
            "claude-3-sonnet",
            "gpt-4-turbo", 
            "gpt-4",
            "claude-3-haiku",
            "gpt-3.5-turbo",
            "gemini-pro"
        ]
        
        for model in preferred_models:
            if model in self.available_models:
                return model
        
        # Fallback to first available
        if self.available_models:
            return list(self.available_models.keys())[0]
        
        raise ValueError("No models available")
    
    def _prepare_messages(
        self, 
        query: str, 
        context: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """เตรียม messages สำหรับ LLM"""
        messages = []
        
        # Add system prompt
        messages.append({
            "role": "system",
            "content": self.default_system_prompt
        })
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current query with context
        user_message = f"""Context:
{context}

Question: {query}

กรุณาตอบคำถามโดยอิงจากข้อมูลใน Context ที่ให้มา และระบุแหล่งที่มาหากเป็นไปได้"""
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _convert_to_anthropic_format(self, messages: List[Dict]) -> List[Dict]:
        """แปลง messages ให้เข้ากับ Anthropic format"""
        # Remove system message for Anthropic
        user_messages = [msg for msg in messages if msg["role"] != "system"]
        return user_messages
    
    def _map_to_anthropic_model(self, model_name: str) -> str:
        """แปลง model name ให้เข้ากับ Anthropic"""
        mapping = {
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-opus": "claude-3-opus-20240229"
        }
        return mapping.get(model_name, "claude-3-sonnet-20240229")
    
    async def stream_generate(self, request: GenerationRequest):
        """สำหรับ streaming response (อนาคต)"""
        # TODO: Implement streaming generation
        pass
    
    def get_available_models(self) -> List[str]:
        """รายการ model ที่ใช้งานได้"""
        return list(self.available_models.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """ตรวจสอบสถานะของ Generator"""
        health_status = {
            "available_models": len(self.available_models),
            "services": {}
        }
        
        # Check each service
        service_health = await api_manager.health_check_all()
        for service_name, status in service_health.items():
            health_status["services"][service_name] = status.success
        
        return health_status

# Global generator manager instance
generator_manager = GeneratorManager()