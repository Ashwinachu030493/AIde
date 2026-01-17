# Changelog

All notable changes to AIde will be documented in this file.

## [1.0.0] - 2026-01-17

### 🎉 Initial Production Release

AIde is now production-ready! This release includes all core features for a local-first AI coding assistant.

### ✨ Features

#### Core System
- **AI Chat** - Context-aware conversations with your codebase
- **Document Ingestion** - Parse and index Python, JavaScript, TypeScript, and more
- **Vector Search** - ChromaDB-powered semantic code search
- **Code Auditor** - Automated code quality analysis with persistent findings

#### Dashboard
- **Project Health Score** - Overall code quality metrics
- **Usage Tracking** - LLM token usage and cost estimation
- **File Index Status** - Track indexed files and chunks
- **Activity Timeline** - Recent actions at a glance

#### Settings
- **Multi-Provider Support** - OpenAI, Anthropic, Groq
- **Encrypted API Keys** - Secure local storage
- **Customizable Preferences** - Theme, model selection, auto-ingest

#### VS Code Extension
- **Tabbed Interface** - Home, Chat, Audit, Settings views
- **Activity Bar Integration** - Quick access via sidebar icon
- **Real-time Updates** - Dashboard refreshes automatically

### 🔧 Technical Details
- **Database:** SQLite (local file)
- **Vector Store:** ChromaDB with SentenceTransformer embeddings
- **LLM Client:** LiteLLM with automatic fallback
- **Parser:** Tree-sitter + Regex + Line-based fallback

### 📦 Installation
```bash
# 1. Install VS Code Extension
code --install-extension aide-vscode-1.0.0.vsix

# 2. Start Server
cd server
pip install -r requirements.txt
python -m uvicorn main_enhanced:app --port 8000

# 3. Open AIde in VS Code
# Command Palette: "AIde: Open Dashboard"
```

### 🔒 Security
- API keys encrypted in database
- Localhost-only by default
- No telemetry or external data sharing

---

## [0.3.0] - 2026-01-16 (Phase 3)
- Added persistent audit system
- Implemented user settings with encryption
- Created enhanced LLM client with user-specific keys

## [0.2.0] - 2026-01-15 (Phase 2)
- Implemented code ingestion pipeline
- Added vector store integration
- Created WebSocket chat endpoint

## [0.1.0] - 2026-01-14 (Phase 1)
- Initial project structure
- Basic FastAPI server
- VS Code extension scaffolding
