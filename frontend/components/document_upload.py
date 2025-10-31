"""
Document Upload Component
สำหรับอัปโหลดและจัดการเอกสาร
"""
import streamlit as st
import requests
from typing import List, Optional
import os

def render_upload_interface(api_url: str = "http://localhost:8000"):
    """Render document upload interface"""
    
    st.subheader("📁 อัปโหลดเอกสาร")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "เลือกไฟล์เอกสาร",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        help="รองรับไฟล์ PDF, Word, Text และ Markdown"
    )
    
    if uploaded_files:
        # Display file info
        st.write("📋 **ไฟล์ที่เลือก:**")
        for file in uploaded_files:
            file_size = len(file.read()) / (1024 * 1024)  # MB
            file.seek(0)  # Reset file pointer
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {file.name}")
            with col2:
                st.write(f"{file_size:.2f} MB")
        
        # Upload button
        if st.button("🚀 อัปโหลดและประมวลผล", type="primary"):
            return upload_documents(uploaded_files, api_url)
    
    return None

def upload_documents(files: List, api_url: str) -> Optional[dict]:
    """Upload documents to the API"""
    
    try:
        with st.spinner("🔄 กำลังอัปโหลดและประมวลผลเอกสาร..."):
            
            # Prepare files for upload
            files_data = []
            for file in files:
                files_data.append(("files", (file.name, file, file.type)))
            
            # Upload to API
            response = requests.post(f"{api_url}/upload", files=files_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Display success message
                st.success("✅ อัปโหลดสำเร็จ!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📚 เอกสารที่ประมวลผล", result.get("documents_processed", 0))
                
                with col2:
                    st.metric("📄 จำนวน chunks", result.get("chunks_created", 0))
                
                with col3:
                    st.metric("⏱️ เวลาประมวลผล", f"{result.get('processing_time', 0):.2f}s")
                
                # Show errors if any
                if result.get("errors"):
                    st.warning("⚠️ มีข้อผิดพลาดบางส่วน:")
                    for error in result["errors"]:
                        st.error(error)
                
                return result
                
            else:
                st.error(f"❌ อัปโหลดล้มเหลว: {response.text}")
                return None
                
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return None

def render_document_status(api_url: str = "http://localhost:8000"):
    """Render document status and statistics"""
    
    try:
        response = requests.get(f"{api_url}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            st.subheader("📊 สถานะเอกสาร")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "📚 เอกสารในระบบ", 
                    stats.get("documents_in_database", 0),
                    help="จำนวนชิ้นส่วนเอกสารที่เก็บในฐานข้อมูล"
                )
            
            with col2:
                st.metric(
                    "🤖 โมเดลที่พร้อมใช้งาน",
                    stats.get("available_models", 0),
                    help="จำนวนโมเดล AI ที่พร้อมใช้งาน"
                )
            
            # Clear documents button
            if st.button("🗑️ ลบเอกสารทั้งหมด", type="secondary"):
                if clear_all_documents(api_url):
                    st.rerun()
    
    except Exception as e:
        st.warning(f"⚠️ ไม่สามารถดึงสถานะเอกสารได้: {str(e)}")

def clear_all_documents(api_url: str) -> bool:
    """Clear all documents from the system"""
    
    try:
        with st.spinner("🗑️ กำลังลบเอกสารทั้งหมด..."):
            response = requests.delete(f"{api_url}/documents")
            
            if response.status_code == 200:
                st.success("✅ ลบเอกสารทั้งหมดเรียบร้อยแล้ว")
                return True
            else:
                st.error(f"❌ ลบเอกสารล้มเหลว: {response.text}")
                return False
                
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return False