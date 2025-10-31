"""
Start FastAPI backend server for Enterprise RAG Chatbot
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the FastAPI server"""
    try:
        import uvicorn
        from backend.api.main import app
        from config.environment import env_center
        
        print("🚀 Starting Enterprise RAG Chatbot API Server...")
        print(f"📍 Host: {env_center.server_config.api_host}")
        print(f"🚪 Port: {env_center.server_config.api_port}")
        print(f"🌐 URL: http://localhost:{env_center.server_config.api_port}")
        print(f"📚 Docs: http://localhost:{env_center.server_config.api_port}/docs")
        print("-" * 50)
        
        uvicorn.run(
            "backend.api.main:app",
            host=env_center.server_config.api_host,
            port=env_center.server_config.api_port,
            reload=env_center.server_config.debug,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down API server...")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())