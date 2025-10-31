"""
Document Manager - จัดการเอกสารและ Document Chunks
ตาม RAG Architecture: Documents → Document chunks
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from dataclasses import dataclass

from backend.components.documents.processor import DocumentProcessor
from backend.components.documents.chunking import DocumentChunker
from backend.components.documents.ocr import OCRProcessor
from config.environment import env_center

@dataclass
class DocumentChunk:
    """Document chunk with metadata"""
    id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    chunk_index: int
    embedding: Optional[List[float]] = None

class DocumentManager:
    """จัดการการประมวลผลเอกสารและแบ่ง chunks"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.chunker = DocumentChunker()
        self.ocr_processor = OCRProcessor(
            languages=env_center.ocr_config.easyocr_languages,
            confidence_threshold=env_center.ocr_config.confidence_threshold
        )
    
    async def process_document(self, file_path: Path) -> List[DocumentChunk]:
        """
        ประมวลผลเอกสารและแบ่งเป็น chunks
        
        Args:
            file_path: Path to document file
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            # 1. Extract text from document
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # OCR for image files
                text_content = await self.ocr_processor.extract_text_async(str(file_path))
                file_type = "image"
            else:
                # Regular document processing
                text_content = await self.processor.extract_text_async(str(file_path))
                file_type = "document"
            
            if not text_content:
                raise ValueError(f"No text extracted from {file_path}")
            
            # 2. Split into chunks
            chunks = self.chunker.chunk_text(
                text_content,
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # 3. Create DocumentChunk objects
            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    id=f"{file_path.stem}_{i}",
                    content=chunk_text,
                    metadata={
                        "source_file": str(file_path),
                        "file_type": file_type,
                        "chunk_size": len(chunk_text),
                        "language_detected": self._detect_language(chunk_text)
                    },
                    source=str(file_path),
                    chunk_index=i
                )
                document_chunks.append(chunk)
            
            return document_chunks
            
        except Exception as e:
            raise Exception(f"Error processing document {file_path}: {str(e)}")
    
    async def process_batch(self, file_paths: List[Path]) -> List[DocumentChunk]:
        """ประมวลผลเอกสารหลายไฟล์พร้อมกัน"""
        tasks = [self.process_document(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_chunks = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error processing document: {result}")
                continue
            all_chunks.extend(result)
        
        return all_chunks
    
    def _detect_language(self, text: str) -> str:
        """ตระหนักภาษาของข้อความ (แบบง่าย)"""
        # Simple language detection
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9faf')
        
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "unknown"
        
        thai_ratio = thai_chars / total_chars
        japanese_ratio = japanese_chars / total_chars
        
        if thai_ratio > 0.3:
            return "thai"
        elif japanese_ratio > 0.3:
            return "japanese"
        else:
            return "english"

# Global document manager instance
document_manager = DocumentManager()