"""
FastAPI application for Enterprise RAG Chatbot
Updated to use new RAG Pipeline architecture
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import uvicorn
from pathlib import Path
import asyncio
import tempfile

# Import RAG components
from backend.core.rag_pipeline import rag_pipeline, RAGPipelineConfig, DocumentIngestionResult, QueryResult
from config.environment import env_center

# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    question: str
    conversation_history: Optional[List[Dict]] = None
    model_preference: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    model_used: str
    metadata: Dict[str, Any]

class UploadResponse(BaseModel):
    success: bool
    documents_processed: int
    chunks_created: int
    processing_time: float
    errors: Optional[List[str]] = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Enterprise RAG Chatbot API",
    description="AI-powered knowledge management with OCR support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline initialization
@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup."""
    try:
        await rag_pipeline.initialize()
        logger.info("✅ RAG Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Pipeline: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Enterprise RAG Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        health_status = await rag_pipeline.health_check()
        
        return {
            "status": "healthy" if health_status["pipeline_initialized"] else "initializing",
            "pipeline_initialized": health_status["pipeline_initialized"],
            "services": health_status["services"],
            "components": health_status["components"],
            "database": health_status["database"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process multiple documents."""
    try:
        # Create temporary files
        temp_files = []
        
        for file in files:
            # Validate file type
            file_extension = Path(file.filename).suffix.lower().lstrip('.')
            if file_extension not in ["pdf", "docx", "txt", "md"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_extension}"
                )
            
            # Validate file size (10MB limit)
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file.filename}. Max size: 10MB"
                )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(content)
                temp_files.append(Path(tmp_file.name))
        
        try:
            # Ingest documents
            result = await rag_pipeline.ingest_documents(temp_files)
            
            return UploadResponse(
                success=result.success,
                documents_processed=result.documents_processed,
                chunks_created=result.chunks_created,
                processing_time=result.processing_time,
                errors=result.errors
            )
                
        finally:
            # Clean up temporary files
            for tmp_file_path in temp_files:
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents and get AI response."""
    try:
        result = await rag_pipeline.query(
            question=request.question,
            conversation_history=request.conversation_history,
            model_preference=request.model_preference
        )
        
        return QueryResponse(
            query=result.query,
            answer=result.answer,
            sources=[{
                "content": source.content,
                "source": source.source,
                "similarity_score": source.similarity_score,
                "metadata": source.metadata
            } for source in result.sources],
            confidence_score=result.confidence_score,
            processing_time=result.processing_time,
            model_used=result.model_used,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    try:
        stats = await rag_pipeline.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.get("/models")
async def get_available_models():
    """Get available AI models."""
    try:
        stats = await rag_pipeline.get_stats()
        return {
            "available_models": stats.get("services_status", {}),
            "pipeline_config": stats.get("pipeline_config", {})
        }
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=f"Models failed: {str(e)}")

@app.delete("/documents")
async def clear_all_documents():
    """Clear all documents from the system."""
    try:
        # Reset the RAG pipeline (this should clear the vector database)
        await rag_pipeline.initialize()  # Re-initialize to clear data
        
        return {"message": "All documents cleared successfully"}
            
    except Exception as e:
        logger.error(f"Failed to clear documents: {e}")
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )