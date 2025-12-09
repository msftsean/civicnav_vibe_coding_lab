# Lab Exercises

## Exercise 1: Azure MCP Server Setup (15 min)

Configure `.vscode/mcp.json` for Copilot Agent Mode integration.

**Steps:**
1. Open VS Code settings and enable Agent Mode
2. Review the MCP configuration in `.vscode/mcp.json`
3. Start the Azure MCP Server: `npx -y @azure/mcp@latest server start`
4. Test by asking Copilot to list Azure resources

**Validation:** Copilot can respond to Azure resource queries

---

## Exercise 2: Spec-Driven Development (15 min)

Review SPEC.md and scaffold code with Copilot.

**Steps:**
1. Read `SPEC.md` to understand requirements
2. Ask Copilot to explain the architecture
3. Use Copilot to generate a new model following existing patterns

**Validation:** Generated code follows project conventions

---

## Exercise 3: Build RAG Pipeline (45 min)

Implement hybrid search in `retrieve_agent.py`.

**Steps:**
1. Review `app/tools/search_tool.py` for search capabilities
2. Understand vector, keyword, and semantic search
3. Implement the `run()` method in RetrieveAgent
4. Test with sample queries

**Validation:** Search returns relevant results with scores

---

## Exercise 4: Agent Orchestration (30 min)

Wire the query-retrieve-answer pipeline in `main.py`.

**Steps:**
1. Review the three agents (Query, Retrieve, Answer)
2. Understand data flow between agents
3. Implement the pipeline in the `/api/query` endpoint
4. Test end-to-end with the chat UI

**Validation:** Complete answers with citations returned

---

## Exercise 5: Deploy with azd (20 min)

Deploy to Azure with one command.

**Steps:**
1. Review `azure.yaml` and `infra/main.bicep`
2. Run `azd up` to provision and deploy
3. Verify deployment in Azure portal
4. Test the deployed endpoint

**Validation:** Application accessible via Container Apps URL

---

## Exercise 6: Expose as MCP Server (15 min)

Implement MCP tools for AI assistant integration.

**Steps:**
1. Review `app/mcp/server.py`
2. Understand the tool schema definitions
3. Test tools via Copilot Agent Mode
4. Try: "Use CivicNav to find trash pickup schedule"

**Validation:** Copilot uses CivicNav tools successfully

---

## Extension Challenge: Multi-turn Conversations

Add conversation memory for follow-up questions.

**Hints:**
- Store session history in a dict keyed by session_id
- Pass conversation context to AnswerAgent
- Implement session timeout/cleanup
