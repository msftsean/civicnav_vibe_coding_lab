"""Integration tests for CivicNav tools.

Tests the OpenAI and Search tool wrappers with mocked Azure services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import Category, SearchResult


# Search Tool Tests


@pytest.mark.asyncio
async def test_search_tool_vector_search(
    mock_embedding: list[float],
) -> None:
    """Test vector search functionality."""
    # Arrange
    mock_results = [
        {
            "id": "entry-001",
            "title": "Trash Collection",
            "content": "Trash is collected on Monday.",
            "category": "schedule",
            "service_type": "trash",
            "department": "Public Works",
            "@search.score": 0.95,
            "@search.highlights": {"content": ["<em>Trash</em> is collected on Monday."]},
        }
    ]

    mock_client = MagicMock()
    mock_client.search = MagicMock(return_value=iter(mock_results))

    with patch("app.tools.search_tool.SearchClient", return_value=mock_client):
        from app.tools.search_tool import SearchTool

        tool = SearchTool()
        tool._client = mock_client

        # Act
        results = await tool.hybrid_search(
            query="trash pickup",
            vector=mock_embedding,
            top_k=5,
        )

        # Assert
        assert len(results) == 1
        assert results[0].title == "Trash Collection"
        assert results[0].relevance_score == 0.95


@pytest.mark.asyncio
async def test_search_tool_keyword_search() -> None:
    """Test keyword-only search functionality."""
    # Arrange
    mock_results = [
        {
            "id": "entry-002",
            "title": "Building Permits",
            "content": "Apply for permits at City Hall.",
            "category": "permit",
            "service_type": "building",
            "department": "Planning",
            "@search.score": 0.88,
        }
    ]

    mock_client = MagicMock()
    mock_client.search = MagicMock(return_value=iter(mock_results))

    with patch("app.tools.search_tool.SearchClient", return_value=mock_client):
        from app.tools.search_tool import SearchTool

        tool = SearchTool()
        tool._client = mock_client

        # Act
        results = await tool.keyword_search(
            query="building permit",
            top_k=5,
        )

        # Assert
        assert len(results) == 1
        assert results[0].category == Category.PERMIT


@pytest.mark.asyncio
async def test_search_tool_hybrid_search(
    mock_embedding: list[float],
) -> None:
    """Test hybrid search combining vector, keyword, and semantic."""
    # Arrange
    mock_results = [
        {
            "id": "entry-001",
            "title": "Trash Schedule",
            "content": "Monday and Thursday pickup.",
            "category": "schedule",
            "service_type": "trash",
            "department": "Public Works",
            "@search.score": 0.92,
        },
        {
            "id": "entry-003",
            "title": "Recycling Schedule",
            "content": "Recycling is every Wednesday.",
            "category": "schedule",
            "service_type": "recycling",
            "department": "Public Works",
            "@search.score": 0.85,
        },
    ]

    mock_client = MagicMock()
    mock_client.search = MagicMock(return_value=iter(mock_results))

    with patch("app.tools.search_tool.SearchClient", return_value=mock_client):
        from app.tools.search_tool import SearchTool

        tool = SearchTool()
        tool._client = mock_client

        # Act
        results = await tool.hybrid_search(
            query="when is trash pickup",
            vector=mock_embedding,
            top_k=5,
        )

        # Assert
        assert len(results) == 2
        # Results should be sorted by relevance
        assert results[0].relevance_score >= results[1].relevance_score


@pytest.mark.asyncio
async def test_search_tool_category_filter(
    mock_embedding: list[float],
) -> None:
    """Test search with category filter."""
    # Arrange
    mock_results = [
        {
            "id": "entry-002",
            "title": "Building Permits",
            "content": "How to apply for permits.",
            "category": "permit",
            "service_type": "building",
            "department": "Planning",
            "@search.score": 0.90,
        }
    ]

    mock_client = MagicMock()
    mock_client.search = MagicMock(return_value=iter(mock_results))

    with patch("app.tools.search_tool.SearchClient", return_value=mock_client):
        from app.tools.search_tool import SearchTool

        tool = SearchTool()
        tool._client = mock_client

        # Act
        results = await tool.hybrid_search(
            query="permit application",
            vector=mock_embedding,
            top_k=5,
            category=Category.PERMIT,
        )

        # Assert
        assert len(results) == 1
        assert results[0].category == Category.PERMIT
        # Verify filter was applied in the search call
        call_args = mock_client.search.call_args
        assert "filter" in call_args.kwargs


@pytest.mark.asyncio
async def test_search_tool_get_categories() -> None:
    """Test getting category counts."""
    # Arrange
    mock_facets = {
        "category": [
            {"value": "schedule", "count": 10},
            {"value": "permit", "count": 8},
            {"value": "event", "count": 5},
        ]
    }

    mock_results = MagicMock()
    mock_results.get_facets = MagicMock(return_value=mock_facets)

    mock_client = MagicMock()
    mock_client.search = MagicMock(return_value=mock_results)

    with patch("app.tools.search_tool.SearchClient", return_value=mock_client):
        from app.tools.search_tool import SearchTool

        tool = SearchTool()
        tool._client = mock_client

        # Act
        categories = await tool.get_categories()

        # Assert
        assert categories["schedule"] == 10
        assert categories["permit"] == 8
        assert categories["event"] == 5


# OpenAI Tool Tests


@pytest.mark.asyncio
async def test_openai_tool_chat_completion() -> None:
    """Test chat completion functionality."""
    # Arrange
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.tools.openai_tool.AsyncAzureOpenAI", return_value=mock_client):
        from app.tools.openai_tool import OpenAITool

        tool = OpenAITool()
        tool._client = mock_client

        # Act
        response = await tool.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )

        # Assert
        assert response == "Test response"


@pytest.mark.asyncio
async def test_openai_tool_create_embedding() -> None:
    """Test embedding creation functionality."""
    # Arrange
    mock_embedding = [0.1] * 1536

    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = mock_embedding

    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch("app.tools.openai_tool.AsyncAzureOpenAI", return_value=mock_client):
        from app.tools.openai_tool import OpenAITool

        tool = OpenAITool()
        tool._client = mock_client

        # Act
        embedding = await tool.create_embedding("Test text")

        # Assert
        assert len(embedding) == 1536
        assert embedding == mock_embedding


@pytest.mark.asyncio
async def test_openai_tool_connection_check_success() -> None:
    """Test successful connection check."""
    # Arrange
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ok"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("app.tools.openai_tool.AsyncAzureOpenAI", return_value=mock_client):
        from app.tools.openai_tool import OpenAITool

        tool = OpenAITool()
        tool._client = mock_client

        # Act
        connected = await tool.check_connection()

        # Assert
        assert connected is True


@pytest.mark.asyncio
async def test_openai_tool_connection_check_failure() -> None:
    """Test failed connection check."""
    # Arrange
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Connection failed")
    )

    with patch("app.tools.openai_tool.AsyncAzureOpenAI", return_value=mock_client):
        from app.tools.openai_tool import OpenAITool

        tool = OpenAITool()
        tool._client = mock_client

        # Act
        connected = await tool.check_connection()

        # Assert
        assert connected is False
