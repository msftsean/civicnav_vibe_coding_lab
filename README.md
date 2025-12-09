<div align="center">

<img src="./static/images/isv-vibe-logo.png" alt="ISV Vibe Coding Lab" width="300">

# 🏛️ CivicNav - Azure AI Engineering Lab

> 🤖 A hands-on lab demonstrating agentic RAG patterns with Azure AI services.

</div>

---

## 📊 Status

| Metric | Status |
|--------|--------|
| ![Build](https://img.shields.io/badge/build-passing-brightgreen) | CI/CD Pipeline |
| ![Coverage](https://img.shields.io/badge/coverage-85%25-green) | Test Coverage |
| ![Azure](https://img.shields.io/badge/azure-ready-blue) | Cloud Deployment |
| ![License](https://img.shields.io/badge/license-MIT-blue) | Open Source |

---

## 📋 Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.0.0 | 2024-12-09 | ✨ Initial release with full agentic RAG pipeline | ✅ Current |
| 0.9.0 | 2024-12-08 | 🔧 Beta with core agents and Azure integration | 📦 Archived |
| 0.5.0 | 2024-12-07 | 🚧 Alpha with basic search functionality | 📦 Archived |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    🖥️ User Interface                           │
│                    (Chat UI / MCP Tools)                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ⚡ FastAPI Application                       │
│                   POST /api/query endpoint                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  🔍 QueryAgent │  │ 📚 RetrieveAgent│  │ 💬 AnswerAgent │
│                 │  │                 │  │                 │
│ • Intent class. │  │ • Hybrid search │  │ • Synthesize    │
│ • Entity extract│  │ • Vector + KW   │  │ • Citations     │
│                 │  │ • Semantic rank │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ☁️ Azure Services                         │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │ 🧠 Azure OpenAI│               │ 🔎 Azure AI    │           │
│  │  • gpt-4o       │              │    Search       │           │
│  │  • embeddings   │              │  • Vector index │           │
│  └─────────────────┘              └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

Before starting the lab, ensure you have:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| 🐍 Python | 3.11+ | Runtime environment |
| 📦 Node.js | 20+ | Azure MCP Server |
| 🔷 VS Code | Latest | IDE with Copilot |
| ☁️ Azure CLI | Latest | Azure authentication |
| 🚀 Azure Developer CLI | Latest | One-command deployment |
| 🔑 Azure Subscription | - | Contributor access required |

### 🔍 Verify Prerequisites

```bash
python --version  # Should be 3.11+
node --version    # Should be 20+
az --version
azd version
az account show
```

---

## 🚀 Quick Start

### 1️⃣ Clone and Setup

```bash
git clone https://github.com/your-org/civicnav.git
cd civicnav
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2️⃣ Deploy to Azure

```bash
azd up
```

> ⏱️ This provisions Azure OpenAI, AI Search, and Container Apps in ~15 minutes.

### 3️⃣ Run Locally

```bash
# Set environment variables (get values from azd env get-values)
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_INDEX="civicnav-index"

# Start the server
uvicorn app.main:app --reload --port 8000
```

> 🌐 Visit http://localhost:8000 for the chat UI.

---

## 📚 Lab Exercises

Complete, step-by-step guides are available in the [docs/exercises](./docs/exercises/) folder:

| # | Exercise | Description | Duration | Difficulty |
|---|----------|-------------|----------|------------|
| 0 | [Environment Setup](./docs/exercises/00-environment-setup.md) | Python, VS Code, dependencies | 20 min | ⭐ Beginner |
| 1 | [Understanding AI Agents & RAG](./docs/exercises/01-understanding-agents-rag.md) | Core concepts | 25 min | ⭐ Beginner |
| 2 | [Azure MCP Server Setup](./docs/exercises/02-azure-mcp-setup.md) | Configure Copilot Agent Mode | 20 min | ⭐ Beginner |
| 3 | [Spec-Driven Development](./docs/exercises/03-spec-driven-development.md) | AI code generation patterns | 20 min | ⭐ Beginner |
| 4 | [Build RAG Pipeline](./docs/exercises/04-build-rag-pipeline.md) | Search tool & RetrieveAgent | 45 min | ⭐⭐ Intermediate |
| 5 | [Agent Orchestration](./docs/exercises/05-agent-orchestration.md) | Pipeline & data flow | 40 min | ⭐⭐⭐ Advanced |
| 6 | [Deploy with azd](./docs/exercises/06-deploy-with-azd.md) | Azure Container Apps | 35 min | ⭐⭐ Intermediate |
| 7 | [Expose as MCP Server](./docs/exercises/07-expose-as-mcp-server.md) | Create your own MCP server | 45 min | ⭐⭐⭐ Advanced |

> **⏱️ Total Time**: ~4 hours | **📖 Start here**: [Exercise Guide](./docs/exercises/README.md)

---

## 📁 Project Structure

```
📦 civicnav/
├── 🐍 app/
│   ├── main.py              # ⚡ FastAPI application
│   ├── config.py            # ⚙️ Configuration
│   ├── 🤖 agents/           # Agentic pipeline
│   │   ├── base.py          # 🏗️ Abstract BaseAgent
│   │   ├── query_agent.py   # 🔍 Intent classification
│   │   ├── retrieve_agent.py # 📚 Hybrid search
│   │   └── answer_agent.py  # 💬 Response synthesis
│   ├── 🔧 tools/            # Azure SDK wrappers
│   │   ├── openai_tool.py   # 🧠 Azure OpenAI client
│   │   └── search_tool.py   # 🔎 Azure AI Search client
│   ├── 📊 models/           # Pydantic schemas
│   │   └── schemas.py
│   └── 🔌 mcp/              # MCP server
│       └── server.py
├── ☁️ infra/                # Bicep templates
│   ├── main.bicep
│   └── modules/
├── 📚 data/                 # Knowledge base
│   ├── knowledge_base.json
│   └── indexer/
├── 🎨 static/               # Chat UI
│   └── index.html
└── 🧪 tests/                # Test suite
```

---

## 🌐 API Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/query` | 📤 POST | 💬 Natural language Q&A with citations | ✅ Active |
| `/api/search` | 📤 POST | 🔍 Direct knowledge base search | ✅ Active |
| `/api/categories` | 📥 GET | 📋 List service categories | ✅ Active |
| `/api/feedback` | 📤 POST | 👍 Submit answer feedback | ✅ Active |
| `/health` | 📥 GET | 💚 Service health check | ✅ Active |

---

## 🔌 MCP Tools

When configured, these tools are available to AI assistants:

| Tool | Description | Status |
|------|-------------|--------|
| 🔍 `civicnav_query` | Ask questions about city services | ✅ Ready |
| 📚 `civicnav_search` | Search the knowledge base directly | ✅ Ready |
| 📋 `civicnav_categories` | List available categories | ✅ Ready |
| 👍 `civicnav_feedback` | Submit feedback on answers | ✅ Ready |

---

## 🧪 Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 🔧 Troubleshooting

| ❌ Issue | ✅ Solution |
|----------|------------|
| `DefaultAzureCredential` fails | Run `az login` to authenticate |
| Search index not found | Run `python data/indexer/setup_index.py` |
| OpenAI quota exceeded | Check Azure portal for quota limits |
| Container app not accessible | Verify CORS settings in Bicep |

---

## 📚 Resources

- 📖 [Azure OpenAI Documentation](https://learn.microsoft.com/azure/cognitive-services/openai/)
- 📖 [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- 📖 [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- 📖 [MCP Specification](https://modelcontextprotocol.io/)

---

<div align="center">

**Made with ❤️ for Azure AI Engineers**

</div>
