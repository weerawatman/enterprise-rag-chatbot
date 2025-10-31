# 🤖 Enterprise RAG Chatbot

**AI-powered document search and chat system with clean RAG architecture**

## 🏗️ RAG Architecture Overview

This project implements a production-ready RAG pipeline with clean separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DOCUMENTS     │───▶│    RETRIEVER    │───▶│   GENERATOR     │
│                 │    │                 │    │                 │
│ • PDF, DOCX     │    │ • Embeddings    │    │ • OpenAI GPT    │
│ • Text, MD      │    │ • ChromaDB      │    │ • Anthropic     │
│ • OCR Support   │    │ • Vector Search │    │ • Google AI     │
│ • Smart Chunk   │    │ • Similarity    │    │ • Context Aware │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                       │
    📄 Process               🔍 Retrieve            🤖 Generate
    & Store                 Contexts                Response
```

## 📁 Clean & Organized Project Structure

```
📁 enterprise-rag-chatbot/        # 🏠 Root Directory (No Nested Confusion)
├── 🔧 backend/                   # 🏗️ Backend RAG System
│   ├── 🌐 api/                   # FastAPI REST API
│   │   ├── routes/               # 🛣️ Modular API Routes
│   │   ├── middleware/           # 🔒 Auth & CORS Middleware
│   │   └── main.py               # 🚀 FastAPI App Entry Point
│   ├── 🧩 components/            # RAG Pipeline Components
│   │   ├── 📄 documents/         # Document Processing System
│   │   │   ├── manager.py        # 📋 Document Manager
│   │   │   ├── processor.py      # ⚙️ File Parser (PDF/DOCX/TXT)
│   │   │   ├── chunking.py       # ✂️ Smart Text Chunking
│   │   │   └── ocr.py           # 👁️ Multi-language OCR
│   │   ├── 🔍 retriever/         # Vector Search Engine
│   │   │   ├── manager.py        # 🎯 Search Manager
│   │   │   └── storage.py        # 🗄️ ChromaDB Integration
│   │   └── 🤖 generator/         # AI Response Generation
│   │       ├── manager.py        # 🎛️ Multi-LLM Manager
│   │       └── rag_agent.py      # 🧠 RAG Logic Engine
│   └── 💎 core/                  # Core System Components
│       ├── rag_pipeline.py       # 🔗 Main RAG Orchestrator
│       └── settings.py          # ⚙️ System Settings
├── 🎨 frontend/                  # User Interface Layer
│   ├── 📊 streamlit/            # Streamlit Web App
│   │   ├── app.py               # 🏠 Main UI Application
│   │   └── streamlit_app.py     # 🔄 Alternative Entry
│   ├── 🧩 components/           # Modular UI Components
│   │   ├── chat_interface.py    # 💬 Chat Interface
│   │   ├── document_upload.py   # 📤 File Upload UI
│   │   └── system_monitor.py    # 📈 System Dashboard
│   └── 🖼️ static/              # Static Assets
├── ⚙️ config/                    # Centralized Configuration
│   ├── environment.py           # 🌍 Environment Manager
│   └── api_services.py          # 🔗 API Services Config
├── 💾 data/                     # Data Storage
│   ├── 📁 uploads/              # File Upload Storage
│   └── 🗄️ chroma_db/           # Vector Database Files
├── 📝 logs/                     # Application Logs
├── 🧪 tests/                    # Test Suite
└── 📋 Root Configuration Files
    ├── .env                     # 🔐 Environment Variables
    ├── .env.example            # 📝 Config Template  
    ├── requirements.txt        # 📦 Python Dependencies
    ├── docker-compose.yml      # 🐳 Docker Setup
    ├── run_api.py             # 🚀 Backend Launcher
    └── run_streamlit.py       # 🎨 Frontend Launcher
```

## ✨ Key Improvements Made

### 🗑️ Removed Unnecessary Complexity
- ❌ Eliminated confusing `context-engineering-intro` nested folder
- ❌ Removed unrelated documentation files (CLAUDE.md, INITIAL.md, etc.)
- ✅ Clean, single-level project structure

### 🏗️ RAG Architecture Compliance  
- ✅ Clear separation: Documents → Retriever → Generator
- ✅ Modular components with specific responsibilities
- ✅ Scalable and maintainable codebase

### 🧩 Modular Frontend Design
- ✅ Separated UI components (chat, upload, monitoring)
- ✅ Reusable interface elements
- ✅ Clean Streamlit application structure

## 🚀 Quick Start Guide

### 1. 📦 Installation
```bash
# Clone repository
git clone [repository-url]
cd enterprise-rag-chatbot

# Install dependencies
pip install -r requirements.txt
```

### 2. ⚙️ Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys:
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 3. 🚀 Launch System
```bash
# Terminal 1: Start Backend API
python run_api.py

# Terminal 2: Start Frontend UI  
python run_streamlit.py
```

### 4. 🌐 Access Application
- **Frontend UI:** http://localhost:8501
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🔧 System Components

### 📄 Document Processing Pipeline
**Location:** `backend/components/documents/`
- **Multi-format Support:** PDF, DOCX, TXT, Markdown
- **OCR Integration:** Thai, English, Japanese text recognition
- **Smart Chunking:** Context-aware text segmentation
- **Language Detection:** Automatic content language identification

### 🔍 Vector Retrieval System
**Location:** `backend/components/retriever/`
- **Embedding Models:** OpenAI text-embedding-3-small/large
- **Vector Database:** ChromaDB with persistence
- **Similarity Search:** Cosine similarity with configurable thresholds
- **Context Building:** Intelligent context window management

### 🤖 AI Generation Engine
**Location:** `backend/components/generator/`
- **Multi-LLM Support:** OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Context Integration:** RAG-enhanced prompt engineering
- **Response Streaming:** Real-time response generation
- **Quality Metrics:** Confidence scoring and source attribution

### 🌐 REST API Layer
**Location:** `backend/api/`
- **Document Upload:** `/upload` - Multi-file processing
- **Query Processing:** `/query` - RAG-powered Q&A
- **System Status:** `/health` - Health monitoring
- **Statistics:** `/stats` - System metrics

### 🎨 Interactive Frontend
**Location:** `frontend/streamlit/`
- **Chat Interface:** Real-time conversation with AI
- **Document Management:** Upload and manage knowledge base
- **System Dashboard:** Monitor performance and status
- **Model Selection:** Choose between different AI models

## 🔐 Security & Configuration

### Environment Variables
```bash
# AI Provider APIs
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# RAG Configuration
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
MAX_CONTEXT_LENGTH=4000
DEFAULT_TOP_K=5

# Server Settings
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t enterprise-rag-chatbot .
docker run -p 8000:8000 -p 8501:8501 enterprise-rag-chatbot
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Test specific component
pytest tests/test_rag_pipeline.py -v
```

## 📈 Monitoring & Observability

### Health Endpoints
- **System Health:** `GET /health`
- **Component Status:** `GET /stats` 
- **Available Models:** `GET /models`

### Logging
- **Application logs:** `logs/` directory
- **Structured logging** with timestamps and levels
- **Error tracking** with stack traces

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/new-component`
3. **Follow** the established architecture patterns
4. **Add tests** for new functionality
5. **Submit** pull request with clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🎯 Enterprise RAG Chatbot** - Production-ready AI document search with clean architecture

*Built with ❤️ for scalable AI applications*