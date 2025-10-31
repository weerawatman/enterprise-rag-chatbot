"""
Document module initialization.
"""

from .processor import document_processor, DocumentProcessor
from .ocr import ocr_processor, OCRProcessor
from .chunking import text_chunker, TextChunker

__all__ = [
    'document_processor',
    'DocumentProcessor',
    'ocr_processor', 
    'OCRProcessor',
    'text_chunker',
    'TextChunker'
]