"""
Test configuration and fixtures.
"""

import pytest
import tempfile
import os
from pathlib import Path
import asyncio

# Configure asyncio event loop for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a sample document for testing purposes.
    It contains multiple paragraphs and sentences.
    
    This document will be used to test various functionality
    of the Enterprise RAG Chatbot system.
    
    The system should be able to process this text,
    create chunks, and store them in the vector database.
    """

@pytest.fixture
def sample_thai_text():
    """Sample Thai text for testing."""
    return """
    นี่คือเอกสารตัวอย่างสำหรับการทดสอบ
    ระบบจะต้องสามารถประมวลผลข้อความภาษาไทยได้
    
    การประมวลผล OCR ภาษาไทยมีความซับซ้อน
    เพราะไม่มีการเว้นวรรคระหว่างคำ
    
    ระบบต้องสามารถแยกข้อความและสร้าง chunks ได้อย่างถูกต้อง
    """

@pytest.fixture
def sample_japanese_text():
    """Sample Japanese text for testing."""
    return """
    これはテスト用のサンプル文書です。
    システムは日本語のテキストを処理できる必要があります。
    
    日本語のOCR処理は複雑です。
    ひらがな、カタカナ、漢字が混在しているからです。
    
    システムは正確にテキストを分割し、チャンクを作成する必要があります。
    """