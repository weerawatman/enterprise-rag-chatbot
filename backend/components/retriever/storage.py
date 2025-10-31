"""
Vector storage and retrieval using ChromaDB.
"""

import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from ..models import DocumentChunk, SearchResult
from ..utils.settings import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """ChromaDB vector storage for document chunks."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="enterprise_documents",
                metadata={"description": "Enterprise document chunks for RAG"}
            )
            
            logger.info(f"Initialized ChromaDB collection with {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Add document chunks to vector store."""
        try:
            if not chunks:
                logger.warning("No chunks to add")
                return False
            
            # Prepare data for ChromaDB
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                metadata = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                metadatas.append(metadata)
            
            # Add to collection (ChromaDB will generate embeddings automatically)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {e}")
            return False
    
    async def search(self, query: str, limit: int = None, filter_conditions: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for similar chunks in vector store."""
        try:
            if limit is None:
                limit = settings.vector_search_limit
            
            # Prepare query parameters
            query_params = {
                "query_texts": [query],
                "n_results": limit
            }
            
            # Add filter if provided
            if filter_conditions:
                query_params["where"] = filter_conditions
            
            # Perform search
            results = self.collection.query(**query_params)
            
            # Convert to SearchResult objects
            search_results = []
            
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    result = SearchResult(
                        document_id=results["metadatas"][0][i]["document_id"],
                        chunk_id=results["ids"][0][i],
                        text=results["documents"][0][i],
                        score=1.0 - results["distances"][0][i],  # Convert distance to similarity
                        metadata=results["metadatas"][0][i]
                    )
                    search_results.append(result)
            
            logger.info(f"Found {len(search_results)} similar chunks for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                # Delete the chunks
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.info(f"No chunks found for document {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            return False
    
    async def update_chunk(self, chunk: DocumentChunk) -> bool:
        """Update a specific chunk in the vector store."""
        try:
            # Delete old chunk
            self.collection.delete(ids=[chunk.id])
            
            # Add updated chunk
            await self.add_chunks([chunk])
            
            logger.info(f"Updated chunk {chunk.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update chunk {chunk.id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            
            return {
                "total_chunks": count,
                "collection_name": self.collection.name,
                "collection_metadata": self.collection.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def reset_collection(self) -> bool:
        """Reset the entire collection (delete all data)."""
        try:
            self.client.delete_collection(name="enterprise_documents")
            self._initialize_client()
            
            logger.warning("Reset ChromaDB collection - all data deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False

# Global vector store instance
vector_store = VectorStore()