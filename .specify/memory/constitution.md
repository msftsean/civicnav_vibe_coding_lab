# CivicNav Constitution

> Governing principles for the CivicNav city services Q&A application

---

## Core Principles

### I. Demo-First Development

All features must work in demo mode without Azure resources:
- Demo tools (`DemoOpenAITool`, `DemoSearchTool`) provide full functionality
- Local knowledge base (`data/knowledge_base.json`) for search operations
- Automatic fallback chain: OpenAI API -> Ollama -> Mock responses
- No feature should require Azure deployment for basic testing

### II. Multi-LLM Support

The application supports multiple LLM providers:
- **OpenAI API**: Primary option for labs (fast, high-quality)
- **Ollama**: Local option (free, private)
- **Azure OpenAI**: Production deployments
- **Mock Mode**: Instant responses without any LLM
- Configuration via environment variables (`USE_OPENAI`, `USE_OLLAMA`)

### III. Agentic Architecture

The three-agent pipeline is the core abstraction:
- **QueryAgent**: Intent classification and entity extraction
- **RetrieveAgent**: Hybrid search (vector + keyword + semantic)
- **AnswerAgent**: Response synthesis with citations
- All agents inherit from `BaseAgent` abstract class
- Sequential orchestration with data passing between stages

### IV. Documentation Standards

All documentation must include:
- **Version History**: Semantic versioning with change dates
- **Status Badges**: Visual indicators of current state
- **Tables**: Structured information presentation
- Emojis for visual clarity (as requested for lab exercises)

### V. Lab-Ready Design

The codebase serves as an educational lab:
- 8 comprehensive exercises (00-07)
- Step-by-step guides with validation checklists
- Quick reference tables and visual diagrams
- Progressive difficulty: Beginner -> Intermediate -> Advanced

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| API | FastAPI | REST endpoints |
| LLM | OpenAI / Ollama / Azure OpenAI | Chat completion |
| Search | Azure AI Search / DemoSearchTool | Hybrid retrieval |
| Deployment | Azure Container Apps + azd | Production hosting |
| Protocol | MCP (Model Context Protocol) | AI tool integration |

---

## Quality Gates

| Gate | Requirement |
|------|-------------|
| Demo Mode | All features work without Azure |
| Health Check | `/health` endpoint returns OK |
| Documentation | Version history maintained |
| Exercises | All 8 exercises have validation steps |

---

## Governance

- This constitution supersedes all other development practices
- Amendments require documentation update and version bump
- SPEC.md must be updated when features change
- All PRs must verify demo mode compatibility

**Version**: 1.0.0 | **Ratified**: 2024-12-09 | **Last Amended**: 2024-12-09
