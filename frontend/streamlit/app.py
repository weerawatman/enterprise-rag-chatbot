"""
Enterprise RAG Chatbot - Streamlit Frontend
Updated to use new RAG Pipeline architecture with modular components
"""
import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time
from pathlib import Path
import sys

# Add paths
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

# Import components
from components.chat_interface import render_chat_interface, get_chat_input, render_quick_questions, render_chat_message
from components.document_upload import render_upload_interface, render_document_status
from components.system_monitor import render_system_monitor, render_model_settings, render_performance_metrics

# Try to import config, fallback to default values
try:
    from config.environment import env_center
    API_BASE_URL = f"http://{env_center.server_config.api_host}:{env_center.server_config.api_port}"
except:
    API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Enterprise RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def call_api(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """Make API call to backend"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        st.error("🚫 Cannot connect to backend API. Please make sure the API server is running.")
        return {"error": "Connection failed"}
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API Error: {e}")
        return {"error": str(e)}
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
        return {"error": str(e)}

def display_source(source: Dict, index: int):
    """Display a source document"""
    with st.expander(f"📄 Source {index + 1} (Similarity: {source['similarity_score']:.3f})"):
        st.write("**Content:**")
        st.write(source['content'])
        
        st.write("**Metadata:**")
        metadata = source['metadata']
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**File:** {metadata.get('source_file', 'Unknown')}")
            st.write(f"**Type:** {metadata.get('file_type', 'Unknown')}")
        
        with col2:
            st.write(f"**Language:** {metadata.get('language_detected', 'Unknown')}")
            st.write(f"**Chunk Size:** {metadata.get('chunk_size', 0)} chars")

def main():
    st.title("🤖 Enterprise RAG Chatbot")
    st.markdown("AI-powered document search with multi-language OCR support")
    
    # Sidebar - System Monitor
    with st.sidebar:
        render_system_monitor(API_BASE_URL)
        st.divider()
        render_document_status(API_BASE_URL)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📤 Upload Documents", "📊 System Monitor", "⚙️ Settings"])
    
    with tab1:
        st.header("💬 Chat Interface")
        
        # Initialize conversation history
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
        
        # Model selection
        try:
            models_data = call_api("/models")
            available_models = list(models_data.get("available_models", {}).keys()) if "error" not in models_data else []
        except:
            available_models = []
        
        if available_models:
            selected_model = st.selectbox("🤖 เลือกโมเดล AI:", available_models)
        else:
            selected_model = None
            st.warning("⚠️ ไม่มีโมเดล AI พร้อมใช้งาน")
        
        # Quick questions
        quick_question = render_quick_questions()
        
        # Display chat history
        render_chat_interface(st.session_state.conversation_history)
        
        # Handle user input (quick question or chat input)
        user_input = quick_question or get_chat_input()
        
        if user_input and available_models:
            # Add user message
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": time.strftime("%H:%M:%S")
            }
            st.session_state.conversation_history.append(user_message)
            
            # Display user message
            render_chat_message(user_message, is_user=True)
            
            # Get AI response
            with st.spinner("🤔 กำลังคิด..."):
                query_data = {
                    "question": user_input,
                    "conversation_history": [
                        {"role": msg["role"], "content": msg["content"]} 
                        for msg in st.session_state.conversation_history[:-1]
                    ] if len(st.session_state.conversation_history) > 1 else None,
                    "model_preference": selected_model
                }
                
                response_data = call_api("/query", "POST", query_data)
                
                if "error" not in response_data:
                    # Create assistant message
                    assistant_message = {
                        "role": "assistant",
                        "content": response_data["answer"],
                        "sources": response_data.get("sources", []),
                        "metadata": {
                            "processing_time": response_data.get("processing_time", 0),
                            "confidence_score": response_data.get("confidence_score", 0),
                            "model_used": response_data.get("model_used", "Unknown")
                        },
                        "timestamp": time.strftime("%H:%M:%S")
                    }
                    
                    st.session_state.conversation_history.append(assistant_message)
                    
                    # Display assistant message
                    render_chat_message(assistant_message, is_user=False)
                    
                else:
                    st.error(f"❌ เกิดข้อผิดพลาด: {response_data['error']}")
        
        # Chat controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ ล้างประวัติการสนทนา", type="secondary"):
                st.session_state.conversation_history = []
                st.rerun()
        
        with col2:
            if st.button("� บันทึกการสนทนา", type="secondary"):
                if st.session_state.conversation_history:
                    # This could be implemented to save conversation
                    st.info("💡 ฟีเจอร์นี้จะถูกพัฒนาในอนาคต")
    
    with tab2:
        st.header("📤 จัดการเอกสาร")
        
        # Document upload interface
        upload_result = render_upload_interface(API_BASE_URL)
        
        if upload_result:
            st.balloons()  # Celebration for successful upload
    
    with tab3:
        st.header("📊 การตรวจสอบระบบ")
        
        # Performance metrics
        render_performance_metrics(API_BASE_URL)
        
        st.divider()
        
        # Detailed system monitor
        render_system_monitor(API_BASE_URL)
    
    with tab4:
        st.header("⚙️ การตั้งค่าระบบ")
        
        # Model settings
        render_model_settings(API_BASE_URL)
        
        st.divider()
        
        # System controls
        st.subheader("🗄️ การจัดการฐานข้อมูล")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ ลบเอกสารทั้งหมด", type="secondary"):
                if st.button("⚠️ ยืนยันการลบ", type="primary"):
                    with st.spinner("กำลังลบเอกสาร..."):
                        response_data = call_api("/documents", "DELETE")
                        if "error" not in response_data:
                            st.success("✅ ลบเอกสารทั้งหมดเรียบร้อยแล้ว")
                            st.rerun()
                        else:
                            st.error(f"❌ ลบเอกสารไม่สำเร็จ: {response_data['error']}")
        
        with col2:
            if st.button("� รีสตาร์ทระบบ", type="secondary"):
                st.info("ℹ️ กรุณารีสตาร์ท API Server ด้วยตนเอง")
        
        st.divider()
        
        # Environment validation  
        st.subheader("🔧 ตรวจสอบการตั้งค่า")
        
        if st.button("� ตรวจสอบสภาพแวดล้อม"):
            with st.spinner("กำลังตรวจสอบ..."):
                try:
                    from config.environment import env_center
                    validations = env_center.validate_environment()
                    
                    st.write("**การตั้งค่า API Services:**")
                    for service, status in validations.items():
                        icon = "✅" if status else "❌"
                        service_name = service.replace("_configured", "").replace("_", " ").title()
                        st.write(f"{icon} {service_name}")
                
                except Exception as e:
                    st.error(f"❌ การตรวจสอบล้มเหลว: {e}")

if __name__ == "__main__":
    main()