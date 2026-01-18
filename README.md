# AIde - AI Coding Assistant

> A local-first AI-powered coding assistant for VS Code with RAG capabilities.

[![Version](https://img.shields.io/badge/version-1.0.6-blue.svg)](https://github.com/aide-dev/aide-vscode/releases)
[![VS Code](https://img.shields.io/badge/VS%20Code-1.80+-green.svg)](https://code.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)](https://python.org/)

## 🚀 Quick Start

### 1. Get the Extension
- **Download:** Get `aide-vscode-1.0.6.vsix` from Releases.
- **Install:**
  ```bash
  code --install-extension aide-vscode-1.0.6.vsix
  ```

### 2. Start the Server
 **Windows (One-Click):**
 Double-click `start_server.bat` in the root folder.

 **Manual:**
 ```bash
 cd server
 pip install -r requirements.txt
 python -m uvicorn main_enhanced:app --port 8000
 ```

### 3. Configure API Keys
1. Open VS Code and click the **AIde icon** (Activity Bar).
2. Go to the **Settings** tab in the Dashboard.
3. Enter your keys (OpenAI, Anthropic, Groq, or Hugging Face).
4. Click **Save Settings**.

## ✨ Features

- **🤖 AI Chat** - Context-aware conversations about your code
- **📚 Document Ingestion** - Index your codebase for semantic search
- **🔍 Code Auditor** - Automated code quality analysis
- **📊 Dashboard** - Project health metrics and usage tracking
- **🔒 Local-First** - Your code never leaves your machine

## 📋 Requirements

| Component | Version |
|-----------|---------|
| VS Code | 1.80.0+ |
| Python | 3.8+ |
| RAM | 4GB+ recommended |

## 🔧 Configuration

### Environment Variables (`server/.env`)

```env
# Database
DATABASE_URL=sqlite:///./aide.db

# ChromaDB
CHROMA_SERVER_HOST=local

# App
APP_ENV=production
SECRET_KEY=your-secret-key-here
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
1. Verify server is running: `curl http://localhost:8000/health`
2. Check VS Code Output panel for errors
3. Reload VS Code window

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
