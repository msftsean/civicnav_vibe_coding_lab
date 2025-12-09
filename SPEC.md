# CivicNav Specification

## Overview

CivicNav is a city services Q&A application that demonstrates agentic RAG (Retrieval-Augmented Generation) patterns using Azure AI services.

## User Stories

### US1: Ask City Services Questions

As a citizen, I want to ask natural language questions about city services so that I can quickly find information without navigating complex government websites.

**Acceptance Criteria:**
- System accepts questions in natural language
- Responses include accurate information with source citations
- Response time under 5 seconds

### US2: Get Relevant Search Results

As a user, I want to search the knowledge base directly so that I can browse available information on a topic.

**Acceptance Criteria:**
- Search returns relevant results sorted by relevance
- Results can be filtered by category
- Results show title, snippet, and relevance score

### US3: Understand Response Sources

As a user, I want to see where answers come from so that I can verify the information and learn more.

**Acceptance Criteria:**
- All answers include citations
- Citations link to source documents
- Citations show relevant excerpts

## Technical Requirements

### Agentic Pipeline

The system uses a three-stage agent pipeline:

1. **QueryAgent**: Classifies user intent and extracts entities
2. **RetrieveAgent**: Performs hybrid search (vector + keyword + semantic)
3. **AnswerAgent**: Synthesizes response with citations

### Azure Services

- **Azure OpenAI**: gpt-4o for chat, text-embedding-3-small for vectors
- **Azure AI Search**: Hybrid search with semantic ranking
- **Azure Container Apps**: Serverless hosting with managed identity

### Authentication

All Azure service calls use `DefaultAzureCredential`:
- Local development: Azure CLI authentication
- Production: Managed identity

### Data Model

**Knowledge Base Entry:**
- id, title, content
- category (schedule, event, report, permit, emergency, general)
- service_type, department, updated_date
- content_vector (1536 dimensions)

**Query Response:**
- answer, citations, intent, latency_ms

## API Contract

See `contracts/api.yaml` for OpenAPI specification.

### Endpoints

- `POST /api/query` - Natural language Q&A
- `POST /api/search` - Direct search
- `GET /api/categories` - List categories
- `POST /api/feedback` - Submit feedback
- `GET /health` - Health check

## MCP Tools

The application exposes tools via Model Context Protocol:

- `civicnav_query` - Ask questions
- `civicnav_search` - Search directly
- `civicnav_categories` - List categories
- `civicnav_feedback` - Submit feedback
