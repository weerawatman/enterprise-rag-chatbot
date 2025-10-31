"""
Streamlit web interface for Enterprise RAG Chatbot.
"""

import streamlit as st
import asyncio
import logging
from pathlib import Path
from typing import List
import tempfile
import os

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models import QueryRequest, Document, UploadResponse, DocumentStatus
from src.document import document_processor
from src.vector import vector_store
from src.agents import rag_agent
from src.utils.settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Ensure required directories exist
settings.ensure_directories()

def init_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "documents" not in st.session_state:
        st.session_state.documents = {}
    if "processing" not in st.session_state:
        st.session_state.processing = False

async def process_uploaded_file(uploaded_file) -> UploadResponse:
    """Process uploaded file and add to vector store."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = Path(tmp_file.name)
        
        # Process document
        document = await document_processor.process_document(tmp_file_path)
        
        # Add to vector store if successful
        if document.metadata.processing_status == DocumentStatus.COMPLETED and document.chunks:
            success = await vector_store.add_chunks(document.chunks)
            if success:
                st.session_state.documents[document.id] = document
                
                return UploadResponse(
                    document_id=document.id,
                    filename=document.metadata.filename,
                    status=DocumentStatus.COMPLETED,
                    message=f"Successfully processed {len(document.chunks)} text chunks"
                )
            else:
                return UploadResponse(
                    document_id=document.id,
                    filename=document.metadata.filename,
                    status=DocumentStatus.FAILED,
                    message="Failed to store document in vector database"
                )
        else:
            return UploadResponse(
                document_id=document.id,
                filename=document.metadata.filename,
                status=DocumentStatus.FAILED,
                message=document.metadata.error_message or "Document processing failed"
            )
            
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        return UploadResponse(
            document_id="",
            filename=uploaded_file.name,
            status=DocumentStatus.FAILED,
            message=f"Upload failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass

async def process_query(query: str) -> str:
    """Process user query and return response."""
    try:
        query_request = QueryRequest(
            query=query,
            session_id="streamlit_session"
        )
        
        response = await rag_agent.process_query(query_request)
        
        # Format response with sources
        formatted_response = response.answer
        
        if response.sources:
            formatted_response += "\n\n**Sources:**\n"
            for i, source in enumerate(response.sources, 1):
                doc_name = source.metadata.get("filename", "Unknown Document")
                formatted_response += f"{i}. {doc_name} (Relevance: {source.score:.2f})\n"
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        return f"I apologize, but I encountered an error: {str(e)}"

def display_file_upload():
    """Display file upload interface."""
    st.sidebar.header("📁 Document Upload")
    
    # File uploader
    uploaded_files = st.sidebar.file_uploader(
        "Choose documents to upload",
        type=settings.allowed_file_types_list,
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(settings.allowed_file_types_list)}"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if st.sidebar.button(f"Process {uploaded_file.name}", key=f"process_{uploaded_file.name}"):
                with st.sidebar.spinner(f"Processing {uploaded_file.name}..."):
                    response = asyncio.run(process_uploaded_file(uploaded_file))
                    
                    if response.status == DocumentStatus.COMPLETED:
                        st.sidebar.success(f"✅ {response.message}")
                    else:
                        st.sidebar.error(f"❌ {response.message}")

def display_chat_interface():
    """Display main chat interface."""
    st.header("💬 Enterprise Knowledge Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query and display response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating response..."):
                response = asyncio.run(process_query(prompt))
                st.markdown(response)
                
                # Add assistant message
                st.session_state.messages.append({"role": "assistant", "content": response})

def display_sidebar_info():
    """Display sidebar information and controls."""
    st.sidebar.header("ℹ️ System Info")
    
    # Vector store stats
    if st.sidebar.button("Refresh Stats"):
        stats = vector_store.get_collection_stats()
        st.sidebar.metric("Total Document Chunks", stats.get("total_chunks", 0))
    
    # Document list
    if st.session_state.documents:
        st.sidebar.subheader("📚 Uploaded Documents")
        for doc_id, document in st.session_state.documents.items():
            st.sidebar.text(f"• {document.metadata.filename}")
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    # System settings
    with st.sidebar.expander("⚙️ Settings"):
        st.write(f"**OCR Languages:** {', '.join(settings.ocr_language_list)}")
        st.write(f"**Max File Size:** {settings.max_file_size_mb}MB")
        st.write(f"**Chunk Size:** {settings.max_chunk_size} words")

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Enterprise RAG Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🤖 Enterprise RAG Chatbot")
    st.markdown("**AI-powered knowledge management with OCR support for Thai, English, and Japanese documents**")
    
    # Initialize session state
    init_session_state()
    
    # Create two columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        display_chat_interface()
    
    with col2:
        display_file_upload()
        st.markdown("---")
        display_sidebar_info()

if __name__ == "__main__":
    main()