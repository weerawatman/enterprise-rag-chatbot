"""
Environment Center - ศูนย์กลางการจัดการ Environment และ API Configuration
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """Configuration for external APIs"""
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    
@dataclass
class DatabaseConfig:
    """Database configuration"""
    chroma_persist_directory: str = "data/chroma_db"
    chroma_collection_name: str = "enterprise_documents"
    
@dataclass
class OCRConfig:
    """OCR service configuration"""
    easyocr_languages: list = None
    tesseract_config: str = "--psm 6"
    confidence_threshold: float = 0.6
    
    def __post_init__(self):
        if self.easyocr_languages is None:
            self.easyocr_languages = ['th', 'en', 'ja']

@dataclass
class ServerConfig:
    """Server configuration"""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_host: str = "0.0.0.0"
    streamlit_port: int = 8501
    debug: bool = False
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]

class EnvironmentCenter:
    """ศูนย์กลางการจัดการ Environment และ Configuration"""
    
    def __init__(self):
        self.api_config = self._load_api_config()
        self.database_config = self._load_database_config()
        self.ocr_config = self._load_ocr_config()
        self.server_config = self._load_server_config()
        
    def _load_api_config(self) -> APIConfig:
        """Load API configuration from environment variables"""
        return APIConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_key=os.getenv("AZURE_OPENAI_KEY")
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma_db"),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "enterprise_documents")
        )
    
    def _load_ocr_config(self) -> OCRConfig:
        """Load OCR configuration"""
        languages = os.getenv("OCR_LANGUAGES", "th,en,ja").split(",")
        return OCRConfig(
            easyocr_languages=languages,
            tesseract_config=os.getenv("TESSERACT_CONFIG", "--psm 6"),
            confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.6"))
        )
    
    def _load_server_config(self) -> ServerConfig:
        """Load server configuration"""
        cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
        return ServerConfig(
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            streamlit_host=os.getenv("STREAMLIT_HOST", "0.0.0.0"),
            streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            cors_origins=cors_origins
        )
    
    def get_api_client_config(self, provider: str) -> Dict[str, Any]:
        """Get API client configuration for specific provider"""
        configs = {
            "openai": {
                "api_key": self.api_config.openai_api_key,
                "base_url": self.api_config.openai_base_url
            },
            "anthropic": {
                "api_key": self.api_config.anthropic_api_key
            },
            "google": {
                "api_key": self.api_config.google_api_key
            },
            "azure_openai": {
                "endpoint": self.api_config.azure_openai_endpoint,
                "api_key": self.api_config.azure_openai_key
            }
        }
        return configs.get(provider, {})
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that required environment variables are set"""
        validations = {
            "openai_configured": bool(self.api_config.openai_api_key),
            "anthropic_configured": bool(self.api_config.anthropic_api_key),
            "google_configured": bool(self.api_config.google_api_key),
            "azure_configured": bool(self.api_config.azure_openai_key and self.api_config.azure_openai_endpoint),
            "database_configured": bool(self.database_config.chroma_persist_directory),
        }
        return validations

# Global environment center instance
env_center = EnvironmentCenter()