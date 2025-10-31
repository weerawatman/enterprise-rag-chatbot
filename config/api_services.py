"""
API Service Manager - จัดการการเชื่อมต่อกับ API Services ต่างๆ
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import httpx
import asyncio
from dataclasses import dataclass

from config.environment import env_center

@dataclass
class APIResponse:
    """Standard API response format"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None

class BaseAPIService(ABC):
    """Base class for API services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
    
    @abstractmethod
    async def initialize(self):
        """Initialize API client"""
        pass
    
    @abstractmethod
    async def health_check(self) -> APIResponse:
        """Check API service health"""
        pass

class OpenAIService(BaseAPIService):
    """OpenAI API Service"""
    
    async def initialize(self):
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.config.get("api_key"),
                base_url=self.config.get("base_url")
            )
            return True
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            return False
    
    async def health_check(self) -> APIResponse:
        """Check OpenAI API health"""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.models.list()
            return APIResponse(success=True, data={"models_count": len(response.data)})
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> APIResponse:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model
            )
            embeddings = [item.embedding for item in response.data]
            return APIResponse(success=True, data=embeddings)
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def chat_completion(self, messages: List[Dict], model: str = "gpt-3.5-turbo") -> APIResponse:
        """Generate chat completion"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            return APIResponse(success=True, data=response.choices[0].message.content)
        except Exception as e:
            return APIResponse(success=False, error=str(e))

class AnthropicService(BaseAPIService):
    """Anthropic API Service"""
    
    async def initialize(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config.get("api_key")
            )
            return True
        except Exception as e:
            print(f"Failed to initialize Anthropic client: {e}")
            return False
    
    async def health_check(self) -> APIResponse:
        """Check Anthropic API health"""
        try:
            if not self.client:
                await self.initialize()
            
            # Simple test message
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return APIResponse(success=True, data={"status": "healthy"})
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def chat_completion(self, messages: List[Dict], model: str = "claude-3-sonnet-20240229") -> APIResponse:
        """Generate chat completion with Claude"""
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=4000,
                messages=messages
            )
            return APIResponse(success=True, data=response.content[0].text)
        except Exception as e:
            return APIResponse(success=False, error=str(e))

class GoogleService(BaseAPIService):
    """Google AI API Service"""
    
    async def initialize(self):
        """Initialize Google AI client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.get("api_key"))
            self.client = genai
            return True
        except Exception as e:
            print(f"Failed to initialize Google AI client: {e}")
            return False
    
    async def health_check(self) -> APIResponse:
        """Check Google AI API health"""
        try:
            if not self.client:
                await self.initialize()
            
            models = list(self.client.list_models())
            return APIResponse(success=True, data={"models_count": len(models)})
        except Exception as e:
            return APIResponse(success=False, error=str(e))

class APIServiceManager:
    """จัดการ API Services ทั้งหมด"""
    
    def __init__(self):
        self.services: Dict[str, BaseAPIService] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all available API services"""
        # OpenAI Service
        openai_config = env_center.get_api_client_config("openai")
        if openai_config.get("api_key"):
            self.services["openai"] = OpenAIService(openai_config)
        
        # Anthropic Service
        anthropic_config = env_center.get_api_client_config("anthropic")
        if anthropic_config.get("api_key"):
            self.services["anthropic"] = AnthropicService(anthropic_config)
        
        # Google Service
        google_config = env_center.get_api_client_config("google")
        if google_config.get("api_key"):
            self.services["google"] = GoogleService(google_config)
    
    async def initialize_all(self):
        """Initialize all services"""
        results = {}
        for name, service in self.services.items():
            try:
                results[name] = await service.initialize()
            except Exception as e:
                results[name] = False
                print(f"Failed to initialize {name}: {e}")
        return results
    
    async def health_check_all(self) -> Dict[str, APIResponse]:
        """Check health of all services"""
        results = {}
        for name, service in self.services.items():
            results[name] = await service.health_check()
        return results
    
    def get_service(self, name: str) -> Optional[BaseAPIService]:
        """Get specific service by name"""
        return self.services.get(name)
    
    def list_available_services(self) -> List[str]:
        """List all available services"""
        return list(self.services.keys())

# Global API service manager
api_manager = APIServiceManager()