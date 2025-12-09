"""MCP server tests for CivicNav.

Tests the MCP tools that expose CivicNav functionality to AI assistants.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import (
    Category,
    Citation,
    IntentClassification,
    SearchResult,
)


@pytest.fixture
def mock_query_response() -> dict:
    """Mock response from query endpoint."""
    return {
        "answer": "Trash is collected every Monday and Thursday.",
        "citations": [
            {
                "entry_id": "entry-001",
                "title": "Trash Collection Schedule",
                "snippet": "Residential trash collection occurs every Monday and Thursday.",
            }
        ],
        "intent": {
            "category": "schedule",
            "confidence": 0.92,
            "entities": [],
        },
        "latency_ms": 450.5,
    }


@pytest.fixture
def mock_search_results() -> list[dict]:
    """Mock search results."""
    return [
        {
            "id": "result-001",
            "entry_id": "entry-001",
            "title": "Trash Collection",
            "content": "Trash is collected Monday and Thursday.",
            "category": "schedule",
            "relevance_score": 0.95,
        }
    ]


@pytest.mark.asyncio
async def test_civicnav_query_tool(mock_query_response: dict) -> None:
    """Test the civicnav_query MCP tool."""
    with patch("app.mcp.server.submit_query_internal", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_query_response

        from app.mcp.server import civicnav_query

        # Act
        result = await civicnav_query("When is trash pickup?")

        # Assert
        assert result is not None
        assert "answer" in result
        assert "citations" in result
        mock_query.assert_called_once_with("When is trash pickup?")


@pytest.mark.asyncio
async def test_civicnav_search_tool(mock_search_results: list[dict]) -> None:
    """Test the civicnav_search MCP tool."""
    with patch("app.mcp.server.search_internal", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {"results": mock_search_results, "total_count": 1}

        from app.mcp.server import civicnav_search

        # Act
        result = await civicnav_search("trash pickup", top_k=5)

        # Assert
        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 1
        mock_search.assert_called_once_with("trash pickup", 5, None)


@pytest.mark.asyncio
async def test_civicnav_categories_tool() -> None:
    """Test the civicnav_categories MCP tool."""
    mock_categories = {
        "categories": [
            {"name": "schedule", "count": 10},
            {"name": "permit", "count": 8},
        ]
    }

    with patch("app.mcp.server.get_categories_internal", new_callable=AsyncMock) as mock_cats:
        mock_cats.return_value = mock_categories

        from app.mcp.server import civicnav_categories

        # Act
        result = await civicnav_categories()

        # Assert
        assert result is not None
        assert "categories" in result
        assert len(result["categories"]) == 2


@pytest.mark.asyncio
async def test_civicnav_feedback_tool() -> None:
    """Test the civicnav_feedback MCP tool."""
    with patch("app.mcp.server.submit_feedback_internal", new_callable=AsyncMock) as mock_feedback:
        mock_feedback.return_value = {"id": "feedback-001", "status": "received"}

        from app.mcp.server import civicnav_feedback

        # Act
        result = await civicnav_feedback(
            answer_id="answer-001",
            rating=5,
            comment="Very helpful!",
        )

        # Assert
        assert result is not None
        assert result["status"] == "received"
        mock_feedback.assert_called_once_with("answer-001", 5, "Very helpful!")


@pytest.mark.asyncio
async def test_civicnav_query_tool_error_handling() -> None:
    """Test error handling in civicnav_query tool."""
    with patch("app.mcp.server.submit_query_internal", new_callable=AsyncMock) as mock_query:
        mock_query.side_effect = Exception("Connection failed")

        from app.mcp.server import civicnav_query

        # Act
        result = await civicnav_query("test query")

        # Assert
        assert result is not None
        assert "error" in result


@pytest.mark.asyncio
async def test_civicnav_search_with_category_filter(mock_search_results: list[dict]) -> None:
    """Test search with category filter."""
    with patch("app.mcp.server.search_internal", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {"results": mock_search_results, "total_count": 1}

        from app.mcp.server import civicnav_search

        # Act
        result = await civicnav_search("pickup", top_k=3, category="schedule")

        # Assert
        mock_search.assert_called_once_with("pickup", 3, "schedule")
