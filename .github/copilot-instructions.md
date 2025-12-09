# CivicNav Copilot Instructions

You are helping develop CivicNav, a city services Q&A application using Azure AI services.

## Architecture

CivicNav uses a three-stage agentic RAG pipeline:

1. **QueryAgent** - Classifies intent (schedule, event, report, permit, emergency, general) and extracts entities
2. **RetrieveAgent** - Performs hybrid search using Azure AI Search (vector + keyword + semantic ranking)
3. **AnswerAgent** - Synthesizes natural language responses with citations from Azure OpenAI

## Key Patterns

### Azure Authentication

Always use `DefaultAzureCredential` for Azure service authentication:

```python
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
```

### Async-First

All Azure SDK calls should be async:

```python
async def search(self, query: str) -> list[SearchResult]:
    results = await self.client.search(...)
    return results
```

### Pydantic Models

Use Pydantic v2 for all data models:

```python
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
```

### Agent Pattern

Agents inherit from BaseAgent and implement async run():

```python
class MyAgent(BaseAgent[InputType, OutputType]):
    async def run(self, input_data: InputType) -> AgentResult:
        # Implementation
        return AgentResult(output=result, reasoning="...", tools_used=self.tools_used)
```

## Project Structure

- `app/agents/` - Agent implementations
- `app/tools/` - Azure SDK wrappers
- `app/models/` - Pydantic schemas
- `app/mcp/` - MCP server
- `infra/` - Bicep templates
- `data/` - Knowledge base

## Available MCP Tools

When Azure MCP Server is configured, you have access to:

- Azure resource management
- CivicNav query and search tools

## Testing

Use pytest with Azure mocks:

```python
@pytest.mark.asyncio
async def test_agent(mock_openai_tool):
    agent = MyAgent()
    result = await agent.execute(input_data)
    assert result.output is not None
```
