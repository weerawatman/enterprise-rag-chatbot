"""
Chat Interface Component
สำหรับแสดงผลการสนทนา และรับ input จากผู้ใช้
"""
import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

def render_chat_message(message: Dict[str, Any], is_user: bool = True):
    """Render a single chat message"""
    
    if is_user:
        with st.chat_message("user"):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])
            
            # Show sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📚 แหล่งข้อมูล", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        st.write(f"**แหล่งที่ {i}:**")
                        st.write(f"📄 {source.get('source', 'Unknown')}")
                        st.write(f"🎯 ความแม่นยำ: {source.get('similarity_score', 0):.2%}")
                        with st.expander(f"เนื้อหาที่เกี่ยวข้อง", expanded=False):
                            st.text(source.get('content', ''))
                        st.divider()
            
            # Show metadata
            if "metadata" in message:
                metadata = message["metadata"]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if "processing_time" in metadata:
                        st.metric("⚡ เวลาประมวลผล", f"{metadata['processing_time']:.2f}s")
                
                with col2:
                    if "confidence_score" in metadata:
                        st.metric("🎯 ความเชื่อมั่น", f"{metadata['confidence_score']:.2%}")
                
                with col3:
                    if "model_used" in metadata:
                        st.metric("🤖 โมเดล", metadata["model_used"])
            
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")

def render_chat_interface(conversation_history: List[Dict[str, Any]]):
    """Render the complete chat interface"""
    
    # Display conversation history
    for message in conversation_history:
        render_chat_message(message, message.get("role") == "user")
    
    return conversation_history

def get_chat_input():
    """Get user input with enhanced features"""
    
    # Chat input
    user_input = st.chat_input("พิมพ์คำถามของคุณที่นี่...")
    
    return user_input

def render_quick_questions():
    """Render quick question buttons"""
    
    st.subheader("💡 คำถามตัวอย่าง")
    
    quick_questions = [
        "เอกสารนี้เกี่ยวกับอะไร?",
        "สรุปเนื้อหาสำคัญให้ฟัง",
        "มีข้อมูลเกี่ยวกับ RAG architecture ไหม?",
        "วิธีการติดตั้งระบบอย่างไร?"
    ]
    
    cols = st.columns(2)
    selected_question = None
    
    for i, question in enumerate(quick_questions):
        col = cols[i % 2]
        with col:
            if st.button(question, key=f"quick_q_{i}", use_container_width=True):
                selected_question = question
    
    return selected_question