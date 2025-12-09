"""API endpoint tests for CivicNav.

Tests all REST API endpoints defined in contracts/api.yaml.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.schemas import (
    Category,
    Citation,
    IntentClassification,
    SearchResult,
)


@pytest.fixture
def mock_pipeline() -> dict:
    """Create mocked pipeline components."""
    intent = IntentClassification(
        category=Category.SCHEDULE,
        confidence=0.92,
        entities=[],
    )

    search_results = [
        SearchResult(
            id="result-001",
            entry_id="entry-001",
            title="Trash Collection Schedule",
            content="Trash is collected every Monday and Thursday.",
            category=Category.SCHEDULE,
            service_type="trash",
            department="Public Works",
            relevance_score=0.95,
        ),
    ]

    citations = [
        Citation(
            entry_id="entry-001",
            title="Trash Collection Schedule",
            snippet="Trash is collected every Monday and Thursday.",
        ),
    ]

    return {
        "intent": intent,
        "search_results": search_results,
        "citations": citations,
        "answer": "Trash is collected every Monday and Thursday in most areas.",
    }


@pytest.mark.asyncio
async def test_submit_query_success(mock_pipeline: dict) -> None:
    """Test successful query submission."""
    # Arrange
    mock_query_agent = MagicMock()
    mock_query_agent.execute = AsyncMock(return_value=MagicMock(
        output=mock_pipeline["intent"],
        reasoning="Classified as schedule query",
        tools_used=["openai"],
        latency_ms=100.0,
    ))

    mock_retrieve_agent = MagicMock()
    mock_retrieve_agent.execute = AsyncMock(return_value=MagicMock(
        output=mock_pipeline["search_results"],
        reasoning="Found 1 relevant result",
        tools_used=["search", "openai"],
        latency_ms=200.0,
    ))

    mock_answer_agent = MagicMock()
    mock_answer_agent.execute = AsyncMock(return_value=MagicMock(
        output={
            "answer": mock_pipeline["answer"],
            "citations": mock_pipeline["citations"],
        },
        reasoning="Synthesized answer from search results",
        tools_used=["openai"],
        latency_ms=150.0,
    ))

    with (
        patch("app.main.QueryAgent", return_value=mock_query_agent),
        patch("app.main.RetrieveAgent", return_value=mock_retrieve_agent),
        patch("app.main.AnswerAgent", return_value=mock_answer_agent),
    ):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/query",
                json={"query": "When is trash pickup?"},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "citations" in data
            assert "intent" in data
            assert "latency_ms" in data


@pytest.mark.asyncio
async def test_submit_query_validation_error() -> None:
    """Test query validation error for too-short query."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Act
        response = await client.post(
            "/api/query",
            json={"query": "ab"},  # Too short (min 3 chars)
        )

        # Assert
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_search_endpoint(mock_pipeline: dict) -> None:
    """Test direct search endpoint."""
    mock_search_tool = MagicMock()
    mock_search_tool.keyword_search = AsyncMock(
        return_value=mock_pipeline["search_results"]
    )

    with patch("app.main.get_search_tool", return_value=mock_search_tool):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act
            response = await client.post(
                "/api/search",
                json={"query": "trash pickup", "top_k": 5},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "total_count" in data


@pytest.mark.asyncio
async def test_categories_endpoint() -> None:
    """Test categories listing endpoint."""
    mock_search_tool = MagicMock()
    mock_search_tool.get_categories = AsyncMock(return_value={
        "schedule": 10,
        "event": 5,
        "permit": 8,
    })

    with patch("app.main.get_search_tool", return_value=mock_search_tool):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get("/api/categories")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "categories" in data
            assert len(data["categories"]) == 3


@pytest.mark.asyncio
async def test_feedback_endpoint() -> None:
    """Test feedback submission endpoint."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Act
        response = await client.post(
            "/api/feedback",
            json={
                "answer_id": str(uuid4()),
                "rating": 5,
                "comment": "Very helpful answer!",
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "received"


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test health check endpoint."""
    mock_openai_tool = MagicMock()
    mock_openai_tool.check_connection = AsyncMock(return_value=True)

    mock_search_tool = MagicMock()
    mock_search_tool.check_connection = AsyncMock(return_value=True)

    with (
        patch("app.main.get_openai_tool", return_value=mock_openai_tool),
        patch("app.main.get_search_tool", return_value=mock_search_tool),
    ):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint_degraded() -> None:
    """Test health endpoint when a service is unavailable."""
    mock_openai_tool = MagicMock()
    mock_openai_tool.check_connection = AsyncMock(return_value=True)

    mock_search_tool = MagicMock()
    mock_search_tool.check_connection = AsyncMock(return_value=False)

    with (
        patch("app.main.get_openai_tool", return_value=mock_openai_tool),
        patch("app.main.get_search_tool", return_value=mock_search_tool),
    ):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act
            response = await client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_deployed_health_check() -> None:
    """Integration test for health endpoint (placeholder for deployment testing)."""
    # This test would be run against a deployed instance
    # For unit testing, we just verify the endpoint structure
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        # Verify response structure
        data = response.json()
        assert "status" in data
        assert "version" in data
