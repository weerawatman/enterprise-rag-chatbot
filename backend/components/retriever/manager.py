"""
Retriever Manager - จัดการ Embedding Model และ Vector Database
ตาม RAG Architecture: Query → Embedding → Vector DB → Query + Context
"""
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass

from backend.components.documents.manager import DocumentChunk
from backend.components.retriever.storage import VectorStorage
from config.api_services import api_manager
from config.environment import env_center

@dataclass
class RetrievalResult:
    """ผลลัพธ์การค้นหา"""
    chunk: DocumentChunk
    similarity_score: float
    rank: int

class RetrieverManager:
    """จัดการการค้นหาและดึงข้อมูลจาก Vector Database"""
    
    def __init__(self):
        self.vector_storage = VectorStorage(
            persist_directory=env_center.database_config.chroma_persist_directory,
            collection_name=env_center.database_config.chroma_collection_name
        )
        self.embedding_service = None
        self._initialize_embedding_service()
    
    def _initialize_embedding_service(self):
        """เริ่มต้น embedding service"""
        # Try to use OpenAI first, fall back to others
        self.embedding_service = api_manager.get_service("openai")
        if not self.embedding_service:
            # Could add other embedding services here
            print("Warning: No embedding service available")
    
    async def add_documents(self, documents: List[DocumentChunk]) -> bool:
        """
        เพิ่มเอกสารลงใน Vector Database
        
        Args:
            documents: List of DocumentChunk objects
            
        Returns:
            Success status
        """
        try:
            # Generate embeddings for all documents
            texts = [doc.content for doc in documents]
            
            if not self.embedding_service:
                raise ValueError("No embedding service available")
            
            embedding_response = await self.embedding_service.generate_embeddings(texts)
            
            if not embedding_response.success:
                raise ValueError(f"Failed to generate embeddings: {embedding_response.error}")
            
            embeddings = embedding_response.data
            
            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Store in vector database
            await self.vector_storage.add_documents_async(documents)
            
            return True
            
        except Exception as e:
            print(f"Error adding documents to vector storage: {e}")
            return False
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        ค้นหาเอกสารที่คล้ายกับ query
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        try:
            # Generate embedding for query
            if not self.embedding_service:
                raise ValueError("No embedding service available")
            
            embedding_response = await self.embedding_service.generate_embeddings([query])
            
            if not embedding_response.success:
                raise ValueError(f"Failed to generate query embedding: {embedding_response.error}")
            
            query_embedding = embedding_response.data[0]
            
            # Search in vector database
            results = await self.vector_storage.search_async(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for i, (chunk, score) in enumerate(results):
                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=score,
                    rank=i + 1
                )
                retrieval_results.append(result)
            
            return retrieval_results
            
        except Exception as e:
            print(f"Error searching similar documents: {e}")
            return []
    
    async def search_by_filters(
        self, 
        query: str, 
        filters: Dict[str, Any] = None, 
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        ค้นหาด้วย filters เพิ่มเติม
        
        Args:
            query: Search query
            filters: Metadata filters
            top_k: Number of results
            
        Returns:
            Filtered retrieval results
        """
        try:
            # Get all results first
            all_results = await self.search_similar(query, top_k * 2)  # Get more for filtering
            
            if not filters:
                return all_results[:top_k]
            
            # Apply filters
            filtered_results = []
            for result in all_results:
                match = True
                for key, value in filters.items():
                    if key not in result.chunk.metadata or result.chunk.metadata[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_results.append(result)
                
                if len(filtered_results) >= top_k:
                    break
            
            return filtered_results
            
        except Exception as e:
            print(f"Error in filtered search: {e}")
            return []
    
    async def get_context_for_query(self, query: str, max_context_length: int = 4000) -> str:
        """
        สร้าง context สำหรับ query
        
        Args:
            query: User query
            max_context_length: Maximum context length
            
        Returns:
            Context string for generation
        """
        try:
            # Search for relevant documents
            results = await self.search_similar(query, top_k=10)
            
            if not results:
                return "ไม่พบข้อมูลที่เกี่ยวข้องในระบบ"
            
            # Build context from results
            context_parts = []
            current_length = 0
            
            for result in results:
                chunk_text = result.chunk.content
                
                # Add source info
                source_info = f"[Source: {result.chunk.metadata.get('source_file', 'Unknown')}]"
                chunk_with_source = f"{source_info}\n{chunk_text}\n"
                
                # Check if adding this chunk exceeds limit
                if current_length + len(chunk_with_source) > max_context_length:
                    break
                
                context_parts.append(chunk_with_source)
                current_length += len(chunk_with_source)
            
            if not context_parts:
                return "ไม่พบข้อมูลที่เกี่ยวข้องในระบบ"
            
            return "\n---\n".join(context_parts)
            
        except Exception as e:
            print(f"Error building context: {e}")
            return f"เกิดข้อผิดพลาดในการค้นหาข้อมูล: {str(e)}"
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """ดูสถิติของ Vector Database"""
        try:
            return await self.vector_storage.get_collection_stats()
        except Exception as e:
            return {"error": str(e)}

# Global retriever manager instance
retriever_manager = RetrieverManager()