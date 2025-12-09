"""CivicNav MCP Server Implementation.

Exposes CivicNav functionality as MCP tools for AI assistant integration.
Tools: civicnav_query, civicnav_search, civicnav_categories, civicnav_feedback
"""

import asyncio
import logging
from typing import Any
from uuid import uuid4

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.agents.query_agent import QueryAgent
from app.agents.retrieve_agent import RetrieveAgent
from app.agents.answer_agent import AnswerAgent
from app.models.schemas import Category, FeedbackRequest
from app.tools.search_tool import get_search_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("civicnav")


# Internal functions that do the actual work


async def submit_query_internal(query: str) -> dict[str, Any]:
    """Process a query through the agentic pipeline."""
    try:
        # Stage 1: Query Agent
        query_agent = QueryAgent()
        query_result = await query_agent.execute(query)
        intent = query_result.output

        # Stage 2: Retrieve Agent
        retrieve_agent = RetrieveAgent()
        retrieve_result = await retrieve_agent.execute((query, intent))
        search_results = retrieve_result.output or []

        # Stage 3: Answer Agent
        answer_agent = AnswerAgent()
        answer_result = await answer_agent.execute((query, search_results, intent))
        answer_data = answer_result.output

        return {
            "answer": answer_data["answer"],
            "citations": [c.model_dump() if hasattr(c, "model_dump") else c
                         for c in answer_data.get("citations", [])],
            "intent": {
                "category": intent.category.value,
                "confidence": intent.confidence,
                "entities": [e.model_dump() for e in intent.entities],
            },
            "latency_ms": query_result.latency_ms + retrieve_result.latency_ms + answer_result.latency_ms,
        }
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"error": str(e)}


async def search_internal(query: str, top_k: int, category: str | None) -> dict[str, Any]:
    """Perform direct search."""
    try:
        search_tool = get_search_tool()
        cat = Category(category) if category else None

        results = await search_tool.keyword_search(
            query=query,
            top_k=top_k,
            category=cat,
        )

        return {
            "results": [r.model_dump() for r in results],
            "total_count": len(results),
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e)}


async def get_categories_internal() -> dict[str, Any]:
    """Get category counts."""
    try:
        search_tool = get_search_tool()
        counts = await search_tool.get_categories()

        return {
            "categories": [
                {"name": name, "count": count}
                for name, count in counts.items()
            ]
        }
    except Exception as e:
        logger.error(f"Categories failed: {e}")
        return {"error": str(e)}


async def submit_feedback_internal(answer_id: str, rating: int, comment: str | None) -> dict[str, Any]:
    """Submit feedback."""
    # In production, this would store to a database
    return {
        "id": str(uuid4()),
        "status": "received",
    }


# MCP Tool definitions


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available CivicNav tools."""
    return [
        Tool(
            name="civicnav_query",
            description="Ask a natural language question about city services. Returns an answer with source citations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask about city services",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="civicnav_search",
            description="Search the city services knowledge base directly without synthesizing an answer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (1-20)",
                        "default": 5,
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (schedule, event, report, permit, emergency, general)",
                        "enum": ["schedule", "event", "report", "permit", "emergency", "general"],
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="civicnav_categories",
            description="List all available service categories and the number of entries in each.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="civicnav_feedback",
            description="Submit feedback on an answer to help improve the system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "answer_id": {
                        "type": "string",
                        "description": "ID of the answer being rated",
                    },
                    "rating": {
                        "type": "integer",
                        "description": "Rating from 1 (poor) to 5 (excellent)",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional feedback comment",
                    },
                },
                "required": ["answer_id", "rating"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool call: {name} with args: {arguments}")

    if name == "civicnav_query":
        result = await civicnav_query(arguments["query"])
    elif name == "civicnav_search":
        result = await civicnav_search(
            arguments["query"],
            arguments.get("top_k", 5),
            arguments.get("category"),
        )
    elif name == "civicnav_categories":
        result = await civicnav_categories()
    elif name == "civicnav_feedback":
        result = await civicnav_feedback(
            arguments["answer_id"],
            arguments["rating"],
            arguments.get("comment"),
        )
    else:
        result = {"error": f"Unknown tool: {name}"}

    import json
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# Standalone tool functions for direct use


async def civicnav_query(query: str) -> dict[str, Any]:
    """Ask a question about city services.

    Args:
        query: Natural language question

    Returns:
        Dict with answer, citations, intent, and latency
    """
    return await submit_query_internal(query)


async def civicnav_search(
    query: str,
    top_k: int = 5,
    category: str | None = None,
) -> dict[str, Any]:
    """Search the knowledge base directly.

    Args:
        query: Search query
        top_k: Number of results (1-20)
        category: Optional category filter

    Returns:
        Dict with results and total_count
    """
    return await search_internal(query, top_k, category)


async def civicnav_categories() -> dict[str, Any]:
    """List available categories.

    Returns:
        Dict with categories list
    """
    return await get_categories_internal()


async def civicnav_feedback(
    answer_id: str,
    rating: int,
    comment: str | None = None,
) -> dict[str, Any]:
    """Submit feedback on an answer.

    Args:
        answer_id: ID of the answer
        rating: 1-5 rating
        comment: Optional comment

    Returns:
        Dict with feedback ID and status
    """
    return await submit_feedback_internal(answer_id, rating, comment)


async def main() -> None:
    """Run the MCP server."""
    logger.info("Starting CivicNav MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
