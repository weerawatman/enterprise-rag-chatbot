"""
Enterprise RAG Chatbot Startup Script (Updated Architecture)
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the streamlit app
if __name__ == "__main__":
    import streamlit.cli
    import sys
    
    # Check if new frontend exists
    new_app_path = project_root / "frontend" / "streamlit" / "app.py"
    old_app_path = project_root / "src" / "web" / "streamlit_app.py"
    
    app_path = new_app_path if new_app_path.exists() else old_app_path
    
    print(f"🚀 Starting Enterprise RAG Chatbot Frontend...")
    print(f"📍 App path: {app_path}")
    print(f"🌐 URL: http://localhost:8501")
    print("-" * 50)
    
    # Set up streamlit arguments
    sys.argv = [
        "streamlit", 
        "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    
    streamlit.cli.main()