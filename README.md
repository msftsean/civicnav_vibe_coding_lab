# CivicNav - Azure AI Engineering Lab

A hands-on lab demonstrating agentic RAG patterns with Azure AI services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Chat UI / MCP Tools)                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                   POST /api/query endpoint                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   QueryAgent    │  │  RetrieveAgent  │  │   AnswerAgent   │
│                 │  │                 │  │                 │
│ • Intent class. │  │ • Hybrid search │  │ • Synthesize    │
│ • Entity extract│  │ • Vector + KW   │  │ • Citations     │
│                 │  │ • Semantic rank │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Services                           │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │  Azure OpenAI   │              │  Azure AI Search│          │
│  │  • gpt-4o       │              │  • Vector index │          │
│  │  • embeddings   │              │  • Semantic rank│          │
│  └─────────────────┘              └─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

Before starting the lab, ensure you have:

- **VS Code** with GitHub Copilot extension (Agent Mode enabled)
- **Azure subscription** with Contributor access
- **Python 3.11+** installed
- **Node.js 20+** installed (for Azure MCP Server)
- **Azure CLI** installed and authenticated (`az login`)
- **Azure Developer CLI (azd)** installed

### Verify Prerequisites

```bash
python --version  # Should be 3.11+
node --version    # Should be 20+
az --version
azd version
az account show
```

## Quick Start

### 1. Clone and Setup

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

### 2. Deploy to Azure

```bash
azd up
```

This provisions Azure OpenAI, AI Search, and Container Apps in ~15 minutes.

### 3. Run Locally

```bash
# Set environment variables (get values from azd env get-values)
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_INDEX="civicnav-index"

# Start the server
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000 for the chat UI.

## Lab Exercises

| Exercise | Duration | Focus |
|----------|----------|-------|
| 1. Azure MCP Server Setup | 15 min | Configure Copilot Agent Mode |
| 2. Spec-Driven Development | 15 min | Scaffold from SPEC.md |
| 3. Build RAG Pipeline | 45 min | Implement hybrid search |
| 4. Agent Orchestration | 30 min | Wire the agentic pipeline |
| 5. Deploy with azd | 20 min | One-command deployment |
| 6. Expose as MCP Server | 15 min | Enable AI tool access |

**Total Time**: ~2.5 hours

## Project Structure

```
civicnav/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── agents/              # Agentic pipeline
│   │   ├── base.py          # Abstract BaseAgent
│   │   ├── query_agent.py   # Intent classification
│   │   ├── retrieve_agent.py # Hybrid search
│   │   └── answer_agent.py  # Response synthesis
│   ├── tools/               # Azure SDK wrappers
│   │   ├── openai_tool.py   # Azure OpenAI client
│   │   └── search_tool.py   # Azure AI Search client
│   ├── models/              # Pydantic schemas
│   │   └── schemas.py
│   └── mcp/                 # MCP server
│       └── server.py
├── infra/                   # Bicep templates
│   ├── main.bicep
│   └── modules/
├── data/                    # Knowledge base
│   ├── knowledge_base.json
│   └── indexer/
├── static/                  # Chat UI
│   └── index.html
└── tests/                   # Test suite
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Natural language Q&A with citations |
| `/api/search` | POST | Direct knowledge base search |
| `/api/categories` | GET | List service categories |
| `/api/feedback` | POST | Submit answer feedback |
| `/health` | GET | Service health check |

## MCP Tools

When configured, these tools are available to AI assistants:

- **civicnav_query**: Ask questions about city services
- **civicnav_search**: Search the knowledge base directly
- **civicnav_categories**: List available categories
- **civicnav_feedback**: Submit feedback on answers

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DefaultAzureCredential` fails | Run `az login` to authenticate |
| Search index not found | Run `python data/indexer/setup_index.py` |
| OpenAI quota exceeded | Check Azure portal for quota limits |
| Container app not accessible | Verify CORS settings in Bicep |

## Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/cognitive-services/openai/)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [MCP Specification](https://modelcontextprotocol.io/)
