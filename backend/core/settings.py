"""
Application configuration and settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Keys
    openai_api_key: str
    
    # Directories
    chroma_persist_directory: str = "./data/chroma_db"
    upload_directory: str = "./data/uploads"
    
    # OCR Configuration
    ocr_languages: str = "th,en,ja"
    ocr_confidence_threshold: float = 0.6
    image_enhancement: bool = True
    
    # Performance
    max_file_size_mb: int = 50
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    vector_search_limit: int = 5
    
    # Web Interface
    streamlit_server_port: int = 8501
    fastapi_port: int = 8000
    fastapi_host: str = "0.0.0.0"
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # AI Models
    default_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # File Processing
    allowed_file_types: str = "pdf,docx,txt,jpg,png,jpeg"
    concurrent_uploads: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def ocr_language_list(self) -> List[str]:
        """Get OCR languages as list."""
        return [lang.strip() for lang in self.ocr_languages.split(",")]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get allowed file types as list."""
        return [ft.strip().lower() for ft in self.allowed_file_types.split(",")]
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.upload_directory).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()