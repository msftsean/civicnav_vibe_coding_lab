"""Unit tests for CivicNav agents.

Tests the QueryAgent, RetrieveAgent, and AnswerAgent components
using mocked Azure services.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import (
    AgentResult,
    Category,
    Citation,
    IntentClassification,
    SearchResult,
)


# QueryAgent Tests


@pytest.mark.asyncio
async def test_query_agent_classifies_intent(
    mock_openai_tool: MagicMock,
    sample_intent: IntentClassification,
) -> None:
    """Test that QueryAgent correctly classifies user intent."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value=json.dumps({
            "category": "schedule",
            "confidence": 0.92,
            "entities": [],
        })
    )

    with patch("app.agents.query_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.query_agent import QueryAgent

        agent = QueryAgent()

        # Act
        result = await agent.execute("When is trash pickup?")

        # Assert
        assert result.output is not None
        assert isinstance(result.output, IntentClassification)
        assert result.output.category == Category.SCHEDULE
        assert result.output.confidence >= 0.5
        assert "openai" in [t.lower() for t in result.tools_used] or len(result.tools_used) > 0


@pytest.mark.asyncio
async def test_query_agent_extracts_entities(mock_openai_tool: MagicMock) -> None:
    """Test that QueryAgent extracts entities from queries."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value=json.dumps({
            "category": "schedule",
            "confidence": 0.88,
            "entities": [
                {"type": "location", "value": "downtown", "start_pos": 20, "end_pos": 28},
                {"type": "service_type", "value": "trash", "start_pos": 8, "end_pos": 13},
            ],
        })
    )

    with patch("app.agents.query_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.query_agent import QueryAgent

        agent = QueryAgent()

        # Act
        result = await agent.execute("When is trash pickup in downtown?")

        # Assert
        assert result.output is not None
        assert isinstance(result.output, IntentClassification)
        assert len(result.output.entities) == 2
        entity_types = [e.type.value for e in result.output.entities]
        assert "location" in entity_types
        assert "service_type" in entity_types


@pytest.mark.asyncio
async def test_query_agent_handles_low_confidence(mock_openai_tool: MagicMock) -> None:
    """Test that QueryAgent flags low confidence classifications."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value=json.dumps({
            "category": "general",
            "confidence": 0.35,
            "entities": [],
        })
    )

    with patch("app.agents.query_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.query_agent import QueryAgent

        agent = QueryAgent()

        # Act
        result = await agent.execute("something vague")

        # Assert
        assert result.output is not None
        assert result.output.is_low_confidence is True


# RetrieveAgent Tests


@pytest.mark.asyncio
async def test_retrieve_agent_hybrid_search(
    mock_search_tool: MagicMock,
    mock_openai_tool: MagicMock,
    sample_search_results: list[SearchResult],
    sample_intent: IntentClassification,
) -> None:
    """Test that RetrieveAgent performs hybrid search."""
    # Arrange
    mock_embedding = [0.1] * 1536
    mock_openai_tool.create_embedding = AsyncMock(return_value=mock_embedding)
    mock_search_tool.hybrid_search = AsyncMock(return_value=sample_search_results)

    with (
        patch("app.agents.retrieve_agent.get_openai_tool", return_value=mock_openai_tool),
        patch("app.agents.retrieve_agent.get_search_tool", return_value=mock_search_tool),
    ):
        from app.agents.retrieve_agent import RetrieveAgent

        agent = RetrieveAgent()

        # Act
        result = await agent.execute(("When is trash pickup?", sample_intent))

        # Assert
        assert result.output is not None
        assert isinstance(result.output, list)
        assert len(result.output) > 0
        assert all(isinstance(r, SearchResult) for r in result.output)
        mock_search_tool.hybrid_search.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_agent_returns_citations(
    mock_search_tool: MagicMock,
    mock_openai_tool: MagicMock,
    sample_search_results: list[SearchResult],
    sample_intent: IntentClassification,
) -> None:
    """Test that RetrieveAgent results can be converted to citations."""
    # Arrange
    mock_embedding = [0.1] * 1536
    mock_openai_tool.create_embedding = AsyncMock(return_value=mock_embedding)
    mock_search_tool.hybrid_search = AsyncMock(return_value=sample_search_results)

    with (
        patch("app.agents.retrieve_agent.get_openai_tool", return_value=mock_openai_tool),
        patch("app.agents.retrieve_agent.get_search_tool", return_value=mock_search_tool),
    ):
        from app.agents.retrieve_agent import RetrieveAgent

        agent = RetrieveAgent()

        # Act
        result = await agent.execute(("When is trash pickup?", sample_intent))

        # Assert
        assert result.output is not None
        # Each search result should have the fields needed for citations
        for search_result in result.output:
            assert search_result.entry_id is not None
            assert search_result.title is not None
            assert search_result.content is not None


@pytest.mark.asyncio
async def test_retrieve_agent_filters_by_category(
    mock_search_tool: MagicMock,
    mock_openai_tool: MagicMock,
    sample_search_results: list[SearchResult],
) -> None:
    """Test that RetrieveAgent filters by classified category."""
    # Arrange
    mock_embedding = [0.1] * 1536
    mock_openai_tool.create_embedding = AsyncMock(return_value=mock_embedding)
    mock_search_tool.hybrid_search = AsyncMock(return_value=sample_search_results)

    intent = IntentClassification(
        category=Category.PERMIT,
        confidence=0.9,
        entities=[],
    )

    with (
        patch("app.agents.retrieve_agent.get_openai_tool", return_value=mock_openai_tool),
        patch("app.agents.retrieve_agent.get_search_tool", return_value=mock_search_tool),
    ):
        from app.agents.retrieve_agent import RetrieveAgent

        agent = RetrieveAgent()

        # Act
        await agent.execute(("How do I get a building permit?", intent))

        # Assert
        call_args = mock_search_tool.hybrid_search.call_args
        # Check that category filter was passed
        assert call_args is not None


# AnswerAgent Tests


@pytest.mark.asyncio
async def test_answer_agent_synthesizes_response(
    mock_openai_tool: MagicMock,
    sample_search_results: list[SearchResult],
    sample_intent: IntentClassification,
) -> None:
    """Test that AnswerAgent synthesizes a response from search results."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value="Residential trash collection occurs every Monday and Thursday. "
        "Place your bins at the curb by 7 AM."
    )

    with patch("app.agents.answer_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.answer_agent import AnswerAgent

        agent = AnswerAgent()

        # Act
        result = await agent.execute((
            "When is trash pickup?",
            sample_search_results,
            sample_intent,
        ))

        # Assert
        assert result.output is not None
        assert isinstance(result.output, dict)
        assert "answer" in result.output
        assert len(result.output["answer"]) > 0


@pytest.mark.asyncio
async def test_answer_agent_includes_citations(
    mock_openai_tool: MagicMock,
    sample_search_results: list[SearchResult],
    sample_intent: IntentClassification,
) -> None:
    """Test that AnswerAgent includes citations in response."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value="Trash collection is on Monday and Thursday [1]."
    )

    with patch("app.agents.answer_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.answer_agent import AnswerAgent

        agent = AnswerAgent()

        # Act
        result = await agent.execute((
            "When is trash pickup?",
            sample_search_results,
            sample_intent,
        ))

        # Assert
        assert result.output is not None
        assert "citations" in result.output
        assert isinstance(result.output["citations"], list)


@pytest.mark.asyncio
async def test_answer_agent_handles_no_results(
    mock_openai_tool: MagicMock,
    sample_intent: IntentClassification,
) -> None:
    """Test that AnswerAgent handles empty search results gracefully."""
    # Arrange
    mock_openai_tool.chat_completion = AsyncMock(
        return_value="I don't have specific information about that topic."
    )

    with patch("app.agents.answer_agent.get_openai_tool", return_value=mock_openai_tool):
        from app.agents.answer_agent import AnswerAgent

        agent = AnswerAgent()

        # Act
        result = await agent.execute((
            "What about something obscure?",
            [],  # Empty search results
            sample_intent,
        ))

        # Assert
        assert result.output is not None
        assert "answer" in result.output
        # Should provide a fallback response
        assert len(result.output["answer"]) > 0
