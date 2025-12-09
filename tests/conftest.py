"""Pytest configuration and fixtures for CivicNav tests.

Provides mock fixtures for Azure services to enable testing without
actual Azure connections.
"""

import json
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.schemas import (
    Category,
    Citation,
    IntentClassification,
    KnowledgeBaseEntry,
    SearchResult,
)


@pytest.fixture
def sample_knowledge_entries() -> list[KnowledgeBaseEntry]:
    """Sample knowledge base entries for testing."""
    return [
        KnowledgeBaseEntry(
            id="entry-001",
            title="Trash Collection Schedule",
            content="Residential trash collection occurs every Monday and Thursday. "
            "Place bins at the curb by 7 AM. Downtown area collection is on Tuesday and Friday. "
            "Holiday schedules may vary - check the city website for updates.",
            category=Category.SCHEDULE,
            service_type="trash",
            department="Public Works",
            updated_date=datetime(2024, 1, 15),
        ),
        KnowledgeBaseEntry(
            id="entry-002",
            title="Building Permit Application",
            content="To apply for a building permit, submit Form BP-100 to the Planning Department. "
            "Required documents include property survey, architectural plans, and contractor license. "
            "Processing takes 2-4 weeks. Fees vary based on project scope.",
            category=Category.PERMIT,
            service_type="building",
            department="Planning",
            updated_date=datetime(2024, 2, 1),
        ),
        KnowledgeBaseEntry(
            id="entry-003",
            title="Emergency Services",
            content="For emergencies, dial 911. For non-emergency police matters, call 555-0100. "
            "Fire department non-emergency line is 555-0200. "
            "The city operates a 24/7 emergency management center.",
            category=Category.EMERGENCY,
            service_type="emergency",
            department="Emergency Services",
            updated_date=datetime(2024, 1, 1),
        ),
    ]


@pytest.fixture
def sample_search_results() -> list[SearchResult]:
    """Sample search results for testing."""
    return [
        SearchResult(
            id="result-001",
            entry_id="entry-001",
            title="Trash Collection Schedule",
            content="Residential trash collection occurs every Monday and Thursday...",
            category=Category.SCHEDULE,
            service_type="trash",
            department="Public Works",
            relevance_score=0.95,
            highlight="Residential <em>trash</em> collection occurs every Monday...",
        ),
        SearchResult(
            id="result-002",
            entry_id="entry-002",
            title="Building Permit Application",
            content="To apply for a building permit, submit Form BP-100...",
            category=Category.PERMIT,
            service_type="building",
            department="Planning",
            relevance_score=0.75,
            highlight=None,
        ),
    ]


@pytest.fixture
def sample_intent() -> IntentClassification:
    """Sample intent classification for testing."""
    return IntentClassification(
        category=Category.SCHEDULE,
        confidence=0.92,
        entities=[],
    )


@pytest.fixture
def sample_citations() -> list[Citation]:
    """Sample citations for testing."""
    return [
        Citation(
            entry_id="entry-001",
            title="Trash Collection Schedule",
            snippet="Residential trash collection occurs every Monday and Thursday.",
        ),
    ]


@pytest.fixture
def mock_openai_response() -> str:
    """Mock OpenAI chat completion response."""
    return json.dumps({
        "category": "schedule",
        "confidence": 0.92,
        "entities": [],
    })


@pytest.fixture
def mock_embedding() -> list[float]:
    """Mock embedding vector (1536 dimensions)."""
    return [0.1] * 1536


@pytest.fixture
def mock_openai_tool(mock_openai_response: str, mock_embedding: list[float]) -> MagicMock:
    """Mock OpenAI tool for testing."""
    mock = MagicMock()
    mock.chat_completion = AsyncMock(return_value=mock_openai_response)
    mock.create_embedding = AsyncMock(return_value=mock_embedding)
    mock.check_connection = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_search_tool(sample_search_results: list[SearchResult]) -> MagicMock:
    """Mock Search tool for testing."""
    mock = MagicMock()
    mock.hybrid_search = AsyncMock(return_value=sample_search_results)
    mock.keyword_search = AsyncMock(return_value=sample_search_results)
    mock.get_categories = AsyncMock(return_value={
        "schedule": 10,
        "event": 5,
        "report": 8,
        "permit": 12,
        "emergency": 3,
        "general": 15,
    })
    mock.check_connection = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock settings for testing."""
    mock = MagicMock()
    mock.azure_openai_endpoint = "https://test-openai.openai.azure.com"
    mock.azure_search_endpoint = "https://test-search.search.windows.net"
    mock.azure_search_index = "test-index"
    mock.app_version = "1.0.0-test"
    mock.is_configured = True
    mock.search_top_k = 5
    mock.embedding_dimensions = 1536
    return mock


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API testing."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def anyio_backend() -> str:
    """Configure pytest-asyncio to use asyncio backend."""
    return "asyncio"


# Patch fixtures for isolating tests from Azure services


@pytest.fixture
def patch_openai(mock_openai_tool: MagicMock) -> Any:
    """Patch the OpenAI tool globally."""
    with patch("app.tools.openai_tool.get_openai_tool", return_value=mock_openai_tool):
        yield mock_openai_tool


@pytest.fixture
def patch_search(mock_search_tool: MagicMock) -> Any:
    """Patch the Search tool globally."""
    with patch("app.tools.search_tool.get_search_tool", return_value=mock_search_tool):
        yield mock_search_tool


@pytest.fixture
def patch_settings(mock_settings: MagicMock) -> Any:
    """Patch settings globally."""
    with patch("app.config.get_settings", return_value=mock_settings):
        yield mock_settings
