# AIde - AI Coding Assistant

> A local-first AI-powered coding assistant for VS Code with RAG capabilities.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/aide-dev/aide-vscode/releases)
[![VS Code](https://img.shields.io/badge/VS%20Code-1.80+-green.svg)](https://code.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)](https://python.org/)

## ✨ Features

- **🤖 AI Chat** - Context-aware conversations about your code
- **📚 Document Ingestion** - Index your codebase for semantic search
- **🔍 Code Auditor** - Automated code quality analysis
- **📊 Dashboard** - Project health metrics and usage tracking
- **🔒 Local-First** - Your code never leaves your machine

## 🚀 Quick Start

### 1. Install the Extension

```bash
# Download from GitHub Releases
code --install-extension aide-vscode-1.0.0.vsix
```

### 2. Start the Server

```bash
cd server
pip install -r requirements.txt
python -m uvicorn main_enhanced:app --port 8000
```

### 3. Configure API Keys

1. Open VS Code
2. Click the AIde icon in the Activity Bar
3. Go to **Settings** tab
4. Enter your API key (OpenAI, Anthropic, or Groq)

### 4. Start Using AIde

- **Dashboard**: View project health and metrics
- **Chat**: Ask questions about your code
- **Audit**: Run code quality checks

## 📋 Requirements

| Component | Version |
|-----------|---------|
| VS Code | 1.80.0+ |
| Python | 3.8+ |
| RAM | 4GB+ recommended |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                VS Code Extension                │
│  ┌─────────┬─────────┬─────────┬─────────┐     │
│  │Dashboard│  Chat   │  Audit  │Settings │     │
│  └────┬────┴────┬────┴────┬────┴────┬────┘     │
└───────┼─────────┼─────────┼─────────┼──────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────┐
│              Python Backend (FastAPI)           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Ingestion│ │   LLM    │ │   Auditor    │    │
│  │  Parser  │ │  Client  │ │   Engine     │    │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘    │
│       │            │              │            │
│       ▼            ▼              ▼            │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ ChromaDB │ │ LiteLLM  │ │   SQLite     │    │
│  │ (Vector) │ │ (Router) │ │  (Storage)   │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
└─────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables (`server/.env`)

```env
# Database
DATABASE_URL=sqlite:///./aide.db

# ChromaDB
CHROMA_SERVER_HOST=local

# LLM Providers (set in Settings UI instead)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=

# App
APP_ENV=development
SECRET_KEY=your-secret-key
```

### Supported Languages

| Language | Parser Mode |
|----------|-------------|
| Python | Tree-sitter / Regex |
| JavaScript | Tree-sitter / Regex |
| TypeScript | Tree-sitter / Regex |
| Java | Regex |
| Go | Regex |
| Rust | Regex |
| C/C++ | Regex |

## 📖 Usage

### Indexing Your Project

1. Open the Dashboard tab
2. Your project files are automatically detected
3. Click "Index Files" to start ingestion
4. Watch the progress in the Files Indexed card

### Chatting with AI

1. Open the Chat tab
2. Type your question
3. AIde retrieves relevant code context
4. Get AI-powered responses with code examples

### Running Audits

1. Open the Audit tab
2. Click "Scan Project"
3. View findings by severity
4. Click on issues for details and fix suggestions

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
netstat -an | findstr 8000

# Use a different port
python -m uvicorn main_enhanced:app --port 8001
```

### Extension not connecting
1. Verify server is running: `curl http://localhost:8000/`
2. Check VS Code Output panel for errors
3. Reload VS Code window

### Database errors
```bash
# Reset database (WARNING: deletes all data)
rm aide.db
python -m uvicorn main_enhanced:app --port 8000
# Tables auto-create on first run
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [LiteLLM](https://github.com/BerriAI/litellm) - LLM routing
- [ChromaDB](https://www.trychroma.com/) - Vector storage
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [VS Code Webview UI Toolkit](https://github.com/microsoft/vscode-webview-ui-toolkit) - UI components
