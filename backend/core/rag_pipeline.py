"""
Enterprise RAG Pipeline - Main orchestrator สำหรับ RAG system
รวม Documents → Retriever → Generator เข้าด้วยกัน
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from dataclasses import dataclass
from datetime import datetime

from backend.components.documents.manager import document_manager, DocumentChunk
from backend.components.retriever.manager import retriever_manager, RetrievalResult
from backend.components.generator.manager import generator_manager, GenerationRequest, GenerationResponse
from config.environment import env_center
from config.api_services import api_manager

@dataclass
class RAGPipelineConfig:
    """Configuration for RAG Pipeline"""
    max_context_length: int = 4000
    top_k_retrieval: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    default_model: Optional[str] = None
    enable_reranking: bool = False

@dataclass  
class DocumentIngestionResult:
    """ผลลัพธ์การเพิ่มเอกสาร"""
    success: bool
    documents_processed: int
    chunks_created: int
    processing_time: float
    errors: List[str] = None

@dataclass
class QueryResult:
    """ผลลัพธ์การตอบคำถาม"""
    query: str
    answer: str
    sources: List[RetrievalResult]
    confidence_score: float
    processing_time: float
    model_used: str
    metadata: Dict[str, Any]

class EnterpriseRAGPipeline:
    """Main RAG Pipeline สำหรับ Enterprise system"""
    
    def __init__(self, config: Optional[RAGPipelineConfig] = None):
        self.config = config or RAGPipelineConfig()
        self.is_initialized = False
        
    async def initialize(self):
        """เริ่มต้น RAG Pipeline"""
        try:
            print("Initializing Enterprise RAG Pipeline...")
            
            # Initialize API services
            await api_manager.initialize_all()
            
            # Check health of all components
            health_status = await self.health_check()
            
            if not any(health_status["services"].values()):
                raise Exception("No API services available")
            
            self.is_initialized = True
            print("✅ Enterprise RAG Pipeline initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG Pipeline: {e}")
            raise
    
    async def ingest_documents(self, file_paths: List[Path]) -> DocumentIngestionResult:
        """
        เพิ่มเอกสารเข้าสู่ระบบ RAG
        
        Args:
            file_paths: List of document file paths
            
        Returns:
            DocumentIngestionResult
        """
        start_time = datetime.now()
        errors = []
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            print(f"📄 Processing {len(file_paths)} documents...")
            
            # Process documents to chunks
            all_chunks = []
            for file_path in file_paths:
                try:
                    chunks = await document_manager.process_document(file_path)
                    all_chunks.extend(chunks)
                    print(f"  ✅ {file_path.name}: {len(chunks)} chunks")
                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {str(e)}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
            
            if not all_chunks:
                raise Exception("No documents were processed successfully")
            
            # Add to vector database
            print(f"🔍 Adding {len(all_chunks)} chunks to vector database...")
            success = await retriever_manager.add_documents(all_chunks)
            
            if not success:
                raise Exception("Failed to add documents to vector database")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = DocumentIngestionResult(
                success=True,
                documents_processed=len(file_paths) - len(errors),
                chunks_created=len(all_chunks),
                processing_time=processing_time,
                errors=errors if errors else None
            )
            
            print(f"✅ Document ingestion completed: {result.documents_processed} docs, {result.chunks_created} chunks")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DocumentIngestionResult(
                success=False,
                documents_processed=0,
                chunks_created=0,
                processing_time=processing_time,
                errors=[str(e)] + errors
            )
    
    async def query(
        self, 
        question: str, 
        conversation_history: Optional[List[Dict]] = None,
        model_preference: Optional[str] = None
    ) -> QueryResult:
        """
        ตอบคำถามด้วย RAG Pipeline
        
        Args:
            question: User question
            conversation_history: Previous conversation
            model_preference: Preferred model to use
            
        Returns:
            QueryResult
        """
        start_time = datetime.now()
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            print(f"🤔 Processing query: {question[:100]}...")
            
            # 1. Retrieve relevant documents
            print("  📚 Searching for relevant documents...")
            sources = await retriever_manager.search_similar(
                question, 
                top_k=self.config.top_k_retrieval
            )
            
            # 2. Build context
            context = await retriever_manager.get_context_for_query(
                question, 
                max_context_length=self.config.max_context_length
            )
            
            # 3. Generate answer
            print("  🤖 Generating answer...")
            generation_request = GenerationRequest(
                query=question,
                context=context,
                conversation_history=conversation_history,
                model_preference=model_preference or self.config.default_model
            )
            
            generation_response = await generator_manager.generate_answer(generation_request)
            
            # 4. Calculate confidence score
            confidence_score = self._calculate_confidence_score(sources, generation_response)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = QueryResult(
                query=question,
                answer=generation_response.answer,
                sources=sources,
                confidence_score=confidence_score,
                processing_time=processing_time,
                model_used=generation_response.model_used,
                metadata={
                    "context_length": len(context),
                    "sources_count": len(sources),
                    "generation_time": generation_response.processing_time,
                    **generation_response.metadata
                }
            )
            
            print(f"✅ Query completed in {processing_time:.2f}s (confidence: {confidence_score:.2f})")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                query=question,
                answer=f"เกิดข้อผิดพลาดในการประมวลผลคำถาม: {str(e)}",
                sources=[],
                confidence_score=0.0,
                processing_time=processing_time,
                model_used="error",
                metadata={"error": str(e)}
            )
    
    def _calculate_confidence_score(
        self, 
        sources: List[RetrievalResult], 
        generation_response: GenerationResponse
    ) -> float:
        """คำนวณคะแนนความเชื่อมั่น"""
        if not sources:
            return 0.1
        
        # Base score from retrieval similarity
        avg_similarity = sum(source.similarity_score for source in sources) / len(sources)
        
        # Adjust based on number of sources
        source_factor = min(len(sources) / 5.0, 1.0)
        
        # Adjust based on generation success
        generation_factor = 1.0 if "error" not in generation_response.metadata else 0.3
        
        confidence = avg_similarity * source_factor * generation_factor
        return min(confidence, 1.0)
    
    async def batch_query(self, questions: List[str]) -> List[QueryResult]:
        """ประมวลผลคำถามหลายข้อพร้อมกัน"""
        tasks = [self.query(question) for question in questions]
        return await asyncio.gather(*tasks)
    
    async def health_check(self) -> Dict[str, Any]:
        """ตรวจสอบสถานะของระบบ RAG"""
        status = {
            "pipeline_initialized": self.is_initialized,
            "services": {},
            "components": {},
            "database": {}
        }
        
        # Check API services
        service_health = await api_manager.health_check_all()
        status["services"] = {name: result.success for name, result in service_health.items()}
        
        # Check generator
        generator_health = await generator_manager.health_check()
        status["components"]["generator"] = generator_health
        
        # Check vector database
        try:
            db_stats = await retriever_manager.get_collection_stats()
            status["database"] = db_stats
        except Exception as e:
            status["database"] = {"error": str(e)}
        
        return status
    
    async def get_stats(self) -> Dict[str, Any]:
        """ดูสถิติของระบบ"""
        try:
            db_stats = await retriever_manager.get_collection_stats()
            generator_stats = await generator_manager.health_check()
            
            return {
                "documents_in_database": db_stats.get("document_count", 0),
                "available_models": generator_stats.get("available_models", 0),
                "services_status": generator_stats.get("services", {}),
                "pipeline_config": {
                    "max_context_length": self.config.max_context_length,
                    "top_k_retrieval": self.config.top_k_retrieval,
                    "chunk_size": self.config.chunk_size,
                    "default_model": self.config.default_model
                }
            }
        except Exception as e:
            return {"error": str(e)}

# Global RAG pipeline instance
rag_pipeline = EnterpriseRAGPipeline()