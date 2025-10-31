"""
System Monitor Component
สำหรับแสดงสถานะระบบและการตั้งค่า
"""
import streamlit as st
import requests
from datetime import datetime
import time

def render_system_monitor(api_url: str = "http://localhost:8000"):
    """Render system monitoring interface"""
    
    st.subheader("🖥️ การตรวจสอบระบบ")
    
    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("สถานะระบบ RAG Chatbot")
    
    with col2:
        auto_refresh = st.checkbox("🔄 รีเฟรชอัตโนมัติ")
    
    # Create placeholder for dynamic updates
    status_container = st.container()
    
    # Get system status
    system_status = get_system_status(api_url)
    
    with status_container:
        render_system_status(system_status)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

def get_system_status(api_url: str) -> dict:
    """Get system health status"""
    
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
    except requests.exceptions.ConnectException:
        return {"status": "offline", "message": "ไม่สามารถเชื่อมต่อ API ได้"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "message": "API ตอบสนองช้า"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def render_system_status(status: dict):
    """Render system status display"""
    
    if status.get("status") == "healthy":
        st.success("✅ ระบบทำงานปกติ")
        
        # Show detailed status
        if "pipeline_initialized" in status:
            st.info(f"🔧 Pipeline: {'✅ พร้อมใช้งาน' if status['pipeline_initialized'] else '❌ ไม่พร้อม'}")
        
        # Services status
        if "services" in status and status["services"]:
            st.write("**📡 สถานะ API Services:**")
            
            cols = st.columns(len(status["services"]))
            for i, (service, is_healthy) in enumerate(status["services"].items()):
                with cols[i]:
                    icon = "✅" if is_healthy else "❌"
                    st.metric(f"{icon} {service}", "พร้อม" if is_healthy else "ไม่พร้อม")
        
        # Components status
        if "components" in status and status["components"]:
            st.write("**🔧 สถานะ Components:**")
            
            for component, component_status in status["components"].items():
                if isinstance(component_status, dict):
                    available_models = component_status.get("available_models", 0)
                    st.metric(f"🤖 {component}", f"{available_models} โมเดล")
        
        # Database status
        if "database" in status and status["database"]:
            db_status = status["database"]
            if "error" not in db_status:
                st.write("**🗄️ สถานะฐานข้อมูล:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 จำนวน chunks", db_status.get("document_count", 0))
                with col2:
                    st.metric("💾 ขนาดฐานข้อมูล", "พร้อมใช้งาน")
            else:
                st.error(f"❌ ฐานข้อมูล: {db_status['error']}")
    
    elif status.get("status") == "offline":
        st.error("❌ ไม่สามารถเชื่อมต่อ API ได้")
        st.write("กรุณาตรวจสอบว่า API Server ทำงานอยู่")
        
    elif status.get("status") == "timeout":
        st.warning("⏳ API ตอบสนองช้า")
        st.write("ระบบอาจมีภาระงานสูง")
        
    else:
        st.error(f"❌ เกิดข้อผิดพลาด: {status.get('message', 'Unknown error')}")
    
    # Show last update time
    st.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')}")

def render_model_settings(api_url: str = "http://localhost:8000"):
    """Render model configuration settings"""
    
    st.subheader("⚙️ การตั้งค่าโมเดล")
    
    try:
        response = requests.get(f"{api_url}/models")
        
        if response.status_code == 200:
            models_info = response.json()
            
            # Available models
            if "available_models" in models_info:
                st.write("**🤖 โมเดลที่พร้อมใช้งาน:**")
                
                available = models_info["available_models"]
                for service_name, is_available in available.items():
                    status_icon = "✅" if is_available else "❌"
                    st.write(f"{status_icon} {service_name}: {'พร้อมใช้งาน' if is_available else 'ไม่พร้อม'}")
            
            # Pipeline config
            if "pipeline_config" in models_info:
                st.write("**⚙️ การตั้งค่า Pipeline:**")
                config = models_info["pipeline_config"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("📏 ความยาว Context สูงสุด", config.get("max_context_length", "N/A"))
                    st.metric("🔍 จำนวน Retrieval", config.get("top_k_retrieval", "N/A"))
                
                with col2:
                    st.metric("📄 ขนาด Chunk", config.get("chunk_size", "N/A"))
                    st.metric("🤖 โมเดลเริ่มต้น", config.get("default_model", "N/A") or "Auto")
        
    except Exception as e:
        st.error(f"❌ ไม่สามารถดึงข้อมูลโมเดลได้: {str(e)}")

def render_performance_metrics(api_url: str = "http://localhost:8000"):
    """Render system performance metrics"""
    
    st.subheader("📈 ประสิทธิภาพระบบ")
    
    try:
        response = requests.get(f"{api_url}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Performance metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📚 เอกสารทั้งหมด", stats.get("documents_in_database", 0))
            
            with col2:
                st.metric("🤖 โมเดลพร้อมใช้", stats.get("available_models", 0))
            
            with col3:
                # This would need to be tracked separately
                st.metric("🔍 Query ทั้งหมด", "N/A", help="จำนวนคำถามที่ถูกประมวลผล")
            
            # Additional metrics can be added here
            # - Response time statistics
            # - Error rates
            # - Resource usage
            
        else:
            st.warning("⚠️ ไม่สามารถดึงข้อมูลประสิทธิภาพได้")
    
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")