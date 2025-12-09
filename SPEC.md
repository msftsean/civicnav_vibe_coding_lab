# 📋 CivicNav Specification

> 🏛️ City services Q&A application demonstrating agentic RAG patterns with Azure AI.

---

## 📊 Status

| Metric | Status |
|--------|--------|
| ![Spec](https://img.shields.io/badge/spec-v2.0.0-brightgreen) | Specification |
| ![Implementation](https://img.shields.io/badge/implementation-complete-brightgreen) | Development |
| ![Testing](https://img.shields.io/badge/testing-passing-brightgreen) | Quality |
| ![Exercises](https://img.shields.io/badge/exercises-8%20total-blue) | Lab Content |

---

## 📋 Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 2.0.0 | 2024-12-09 | 🚀 Multi-LLM support: OpenAI API, Ollama, Azure OpenAI, Mock mode | ✅ Current |
| 1.0.0 | 2024-12-09 | ✨ Complete specification with all user stories | 📦 Archived |
| 0.5.0 | 2024-12-07 | 🚧 Draft with core requirements | 📦 Archived |

---

## 🎯 Overview

CivicNav is a city services Q&A application that demonstrates agentic RAG (Retrieval-Augmented Generation) patterns using Azure AI services.

---

## 👤 User Stories

### 📖 US1: Ask City Services Questions

> As a **citizen**, I want to ask natural language questions about city services so that I can quickly find information without navigating complex government websites.

**✅ Acceptance Criteria:**
| # | Criteria | Status |
|---|----------|--------|
| 1 | System accepts questions in natural language | ✅ Done |
| 2 | Responses include accurate information with source citations | ✅ Done |
| 3 | Response time under 5 seconds | ✅ Done |

---

### 🔍 US2: Get Relevant Search Results

> As a **user**, I want to search the knowledge base directly so that I can browse available information on a topic.

**✅ Acceptance Criteria:**
| # | Criteria | Status |
|---|----------|--------|
| 1 | Search returns relevant results sorted by relevance | ✅ Done |
| 2 | Results can be filtered by category | ✅ Done |
| 3 | Results show title, snippet, and relevance score | ✅ Done |

---

### 📚 US3: Understand Response Sources

> As a **user**, I want to see where answers come from so that I can verify the information and learn more.

**✅ Acceptance Criteria:**
| # | Criteria | Status |
|---|----------|--------|
| 1 | All answers include citations | ✅ Done |
| 2 | Citations link to source documents | ✅ Done |
| 3 | Citations show relevant excerpts | ✅ Done |

---

## ⚙️ Technical Requirements

### 🤖 Agentic Pipeline

The system uses a three-stage agent pipeline:

| Stage | Agent | Responsibility | Status |
|-------|-------|----------------|--------|
| 1️⃣ | 🔍 **QueryAgent** | Classifies user intent and extracts entities | ✅ Implemented |
| 2️⃣ | 📚 **RetrieveAgent** | Performs hybrid search (vector + keyword + semantic) | ✅ Implemented |
| 3️⃣ | 💬 **AnswerAgent** | Synthesizes response with citations | ✅ Implemented |

---

### 🧠 LLM Provider Options

The application supports multiple LLM backends with automatic fallback:

| Provider | Use Case | Configuration | Status |
|----------|----------|---------------|--------|
| 🚀 **OpenAI API** | Fast, high-quality (recommended for labs) | `USE_OPENAI=true`, `OPENAI_API_KEY` | ✅ Implemented |
| 🦙 **Ollama** | Local, private, free | `USE_OLLAMA=true`, `OLLAMA_MODEL` | ✅ Implemented |
| ☁️ **Azure OpenAI** | Production deployments | Azure credentials | ✅ Implemented |
| 🎭 **Mock Mode** | No LLM, instant demo responses | Both flags `false` | ✅ Implemented |

**Fallback Chain:** OpenAI API → Ollama → Mock Mode

---

### 🔧 Demo Mode Tools

Demo mode provides full functionality without Azure resources:

| Tool | Class | Description | Status |
|------|-------|-------------|--------|
| 🧠 **DemoOpenAITool** | `app.tools.openai_tool` | Chat completion via OpenAI API or Ollama | ✅ Implemented |
| 🔍 **DemoSearchTool** | `app.tools.search_tool` | Local JSON knowledge base search | ✅ Implemented |

---

### ☁️ Azure Services (Production)

| Service | Purpose | Model/Tier |
|---------|---------|------------|
| 🧠 Azure OpenAI | Chat completion | gpt-4o |
| 🧠 Azure OpenAI | Embeddings | text-embedding-3-small |
| 🔎 Azure AI Search | Hybrid search | Standard with semantic ranking |
| 📦 Azure Container Apps | Hosting | Serverless with managed identity |

---

### 🔐 Authentication

All Azure service calls use `DefaultAzureCredential`:

| Environment | Method |
|-------------|--------|
| 🖥️ Local development | Azure CLI authentication |
| ☁️ Production | Managed identity |

---

### 📊 Data Model

#### 📚 Knowledge Base Entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `title` | string | Document title |
| `content` | string | Full content |
| `category` | enum | schedule, event, report, permit, emergency, general |
| `service_type` | string | Type of city service |
| `department` | string | Responsible department |
| `updated_date` | date | Last update timestamp |
| `content_vector` | float[1536] | Embedding vector |

#### 💬 Query Response

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Natural language response |
| `citations` | Citation[] | Source references |
| `intent` | IntentClassification | Detected intent |
| `latency_ms` | number | Response time |

---

## 🌐 API Contract

> 📄 See `contracts/api.yaml` for OpenAPI specification.

### 🔗 Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/query` | 📤 POST | 💬 Natural language Q&A | ✅ Active |
| `/api/search` | 📤 POST | 🔍 Direct search | ✅ Active |
| `/api/categories` | 📥 GET | 📋 List categories | ✅ Active |
| `/api/feedback` | 📤 POST | 👍 Submit feedback | ✅ Active |
| `/health` | 📥 GET | 💚 Health check | ✅ Active |

---

## 🔌 MCP Tools

The application exposes tools via Model Context Protocol:

| Tool | Description | Status |
|------|-------------|--------|
| 🔍 `civicnav_query` | Ask questions | ✅ Ready |
| 📚 `civicnav_search` | Search directly | ✅ Ready |
| 📋 `civicnav_categories` | List categories | ✅ Ready |
| 👍 `civicnav_feedback` | Submit feedback | ✅ Ready |

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_OPENAI` | Enable OpenAI API | `true` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | If `USE_OPENAI=true` |
| `USE_OLLAMA` | Enable Ollama fallback | `false` | No |
| `OLLAMA_MODEL` | Ollama model name | `phi3:mini` | If `USE_OLLAMA=true` |
| `OLLAMA_ENDPOINT` | Ollama API URL | `http://localhost:11434` | No |
| `DEMO_MODE` | Force demo mode | `false` | No |

### Configuration Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 Configuration Options                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Option 1: OpenAI API (Recommended for Labs)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ USE_OPENAI=true                                            │ │
│  │ OPENAI_API_KEY=sk-your-key-here                           │ │
│  │ USE_OLLAMA=false                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Option 2: Local Ollama (Free, Private)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ USE_OPENAI=false                                           │ │
│  │ USE_OLLAMA=true                                            │ │
│  │ OLLAMA_MODEL=phi3:mini                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Option 3: Mock Mode Only (No LLM)                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ USE_OPENAI=false                                           │ │
│  │ USE_OLLAMA=false                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Lab Exercises

Complete, step-by-step guides are available in the [docs/exercises](./docs/exercises/) folder:

| # | Exercise | Description | Duration |
|---|----------|-------------|----------|
| 0 | 🛠️ Environment Setup | Python, VS Code, dependencies | 20 min |
| 1 | 🧠 Understanding AI Agents & RAG | Core concepts | 25 min |
| 2 | 🔌 Azure MCP Server Setup | Configure Agent Mode | 20 min |
| 3 | 📝 Spec-Driven Development | Generate code with specs | 20 min |
| 4 | 🔍 Build RAG Pipeline | Search tool and RetrieveAgent | 45 min |
| 5 | 🔗 Agent Orchestration | Multi-agent coordination | 40 min |
| 6 | 🚀 Deploy with azd | Azure Container Apps | 35 min |
| 7 | 🔧 Expose as MCP Server | Create MCP tools | 45 min |

**Total Duration:** ~4 hours

---

<div align="center">

**📋 Specification v2.0.0**

</div>
