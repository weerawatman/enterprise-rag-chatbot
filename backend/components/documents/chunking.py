"""
Text chunking strategies for document processing.
"""

import logging
from typing import List, Dict, Any
import re

from ..models import DocumentChunk
from ..utils.settings import settings

logger = logging.getLogger(__name__)

class TextChunker:
    """Create text chunks for vector storage."""
    
    def __init__(self):
        self.chunk_size = settings.max_chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Thai, Japanese, and basic punctuation
        text = re.sub(r'[^\w\s\u0E00-\u0E7F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences, handling multiple languages."""
        # Pattern for sentence boundaries (works for Thai, English, Japanese)
        sentence_pattern = r'[.!?。！？]\s*'
        
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs."""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def create_overlapping_chunks(self, text: str) -> List[str]:
        """Create overlapping text chunks."""
        chunks = []
        words = text.split()
        
        if len(words) <= self.chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Ensure we don't go backwards
            if start <= 0:
                start = end
        
        return chunks
    
    def create_semantic_chunks(self, text: str) -> List[str]:
        """Create chunks based on semantic boundaries."""
        chunks = []
        
        # First, try to split by paragraphs
        paragraphs = self.split_by_paragraphs(text)
        
        current_chunk = ""
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_words = paragraph.split()
            paragraph_size = len(paragraph_words)
            
            # If paragraph alone exceeds chunk size, split it
            if paragraph_size > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_size = 0
                
                # Split large paragraph into smaller chunks
                para_chunks = self.create_overlapping_chunks(paragraph)
                chunks.extend(para_chunks)
                
            # If adding this paragraph would exceed chunk size
            elif current_size + paragraph_size > self.chunk_size:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with this paragraph
                current_chunk = paragraph
                current_size = paragraph_size
                
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += paragraph_size
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def create_chunks(self, document_id: str, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Create document chunks with metadata."""
        if metadata is None:
            metadata = {}
        
        try:
            # Clean the text
            cleaned_text = self.clean_text(text)
            
            if not cleaned_text:
                logger.warning(f"No text to chunk for document {document_id}")
                return []
            
            # Create semantic chunks
            text_chunks = self.create_semantic_chunks(cleaned_text)
            
            # Convert to DocumentChunk objects
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = {
                    "chunk_index": i,
                    "character_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    **metadata
                }
                
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk_text,
                    metadata=chunk_metadata
                )
                
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Chunking failed for document {document_id}: {e}")
            return []

# Global text chunker instance
text_chunker = TextChunker()