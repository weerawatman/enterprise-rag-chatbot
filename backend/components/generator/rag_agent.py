"""
PydanticAI agent for RAG functionality.
"""

import logging
from typing import List, Optional
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

from ..models import QueryRequest, QueryResponse, SearchResult, ChatMessage
from ..vector import vector_store
from ..utils.settings import settings

logger = logging.getLogger(__name__)

class RAGDependencies(BaseModel):
    """Dependencies for RAG agent."""
    vector_store: object
    max_context_length: int = 8000

class RAGAgent:
    """PydanticAI agent for enterprise knowledge Q&A."""
    
    def __init__(self):
        self.agent = Agent(
            model=f"openai:{settings.default_model}",
            deps_type=RAGDependencies,
            system_prompt=self._get_system_prompt()
        )
        
        # Add tools
        self.agent.tool(self.search_documents)
        
    def _get_system_prompt(self) -> str:
        """Get system prompt for the RAG agent."""
        return """You are an enterprise knowledge assistant that helps users find information from organizational documents.

Your capabilities:
- Search through uploaded documents using semantic similarity
- Provide accurate answers based on retrieved content
- Always cite sources with document names and relevant excerpts
- Handle multi-language content (Thai, English, Japanese)
- Admit when you don't have relevant information

Guidelines:
1. Always search for relevant documents before answering
2. Base your answers on the retrieved content
3. Cite sources clearly with document names
4. If no relevant information is found, say so clearly
5. Provide helpful context and explanations
6. Maintain professional and helpful tone

Response format:
- Start with a direct answer to the question
- Provide detailed explanation based on retrieved content
- End with source citations in format: "Source: [Document Name]"
"""
    
    async def search_documents(self, ctx: RunContext[RAGDependencies], query: str, max_results: int = 5) -> List[SearchResult]:
        """Search for relevant documents.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant document chunks with similarity scores
        """
        try:
            results = await ctx.deps.vector_store.search(
                query=query,
                limit=max_results
            )
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    def _format_context(self, search_results: List[SearchResult]) -> str:
        """Format search results into context for the LLM."""
        if not search_results:
            return "No relevant documents found."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            doc_name = result.metadata.get("filename", "Unknown Document")
            context_parts.append(f"Document {i}: {doc_name}\nContent: {result.text}\nRelevance: {result.score:.2f}\n")
        
        return "\n".join(context_parts)
    
    async def process_query(self, query_request: QueryRequest) -> QueryResponse:
        """Process user query and return response with sources."""
        import time
        start_time = time.time()
        
        try:
            # Create dependencies
            deps = RAGDependencies(
                vector_store=vector_store,
                max_context_length=settings.max_tokens
            )
            
            # Search for relevant documents
            search_results = await self.search_documents(
                ctx=RunContext(deps=deps),
                query=query_request.query,
                max_results=query_request.max_results
            )
            
            # Format context for LLM
            context = self._format_context(search_results)
            
            # Prepare prompt with context
            prompt = f"""Based on the following context from enterprise documents, please answer the user's question.

Context:
{context}

User Question: {query_request.query}

Please provide a comprehensive answer based on the available context. If the context doesn't contain relevant information, please state that clearly."""

            # Get response from LLM
            result = await self.agent.run(
                user_prompt=prompt,
                deps=deps
            )
            
            processing_time = time.time() - start_time
            
            return QueryResponse(
                answer=result.data,
                sources=search_results,
                session_id=query_request.session_id or "default",
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            processing_time = time.time() - start_time
            
            return QueryResponse(
                answer=f"I apologize, but I encountered an error while processing your question: {str(e)}",
                sources=[],
                session_id=query_request.session_id or "default",
                processing_time=processing_time
            )

# Global RAG agent instance
rag_agent = RAGAgent()