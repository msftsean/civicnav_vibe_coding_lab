"""RetrieveAgent for hybrid search retrieval.

This agent performs hybrid search (vector + keyword + semantic) to
find relevant knowledge base entries for the user's query.
"""

import logging
from typing import Tuple

from app.agents.base import BaseAgent
from app.models.schemas import AgentResult, IntentClassification, SearchResult
from app.tools.openai_tool import get_openai_tool
from app.tools.search_tool import get_search_tool
from app.config import get_settings

logger = logging.getLogger(__name__)


class RetrieveAgent(BaseAgent[Tuple[str, IntentClassification], list[SearchResult]]):
    """Agent for retrieving relevant knowledge base entries.

    Takes a tuple of (query, intent) and returns a list of SearchResult
    objects sorted by relevance using hybrid search.
    """

    def __init__(self) -> None:
        """Initialize the RetrieveAgent."""
        super().__init__("RetrieveAgent")
        self.openai_tool = get_openai_tool()
        self.search_tool = get_search_tool()
        self.settings = get_settings()

    async def run(
        self, input_data: Tuple[str, IntentClassification]
    ) -> AgentResult:
        """Retrieve relevant documents using hybrid search.

        Args:
            input_data: Tuple of (query_text, intent_classification)

        Returns:
            AgentResult containing list of SearchResult
        """
        query, intent = input_data
        logger.info(f"RetrieveAgent searching for: {query[:50]}...")

        # Generate embedding for vector search
        self.use_tool("openai_embedding")
        try:
            embedding = await self.openai_tool.create_embedding(query)
        except Exception as e:
            logger.warning(f"Embedding failed, falling back to keyword search: {e}")
            embedding = None

        # Perform hybrid search
        self.use_tool("search_hybrid")

        # Use category filter if high confidence
        category_filter = intent.category if intent.confidence >= 0.7 else None

        if embedding:
            results = await self.search_tool.hybrid_search(
                query=query,
                vector=embedding,
                top_k=self.settings.search_top_k,
                category=category_filter,
            )
        else:
            # Fallback to keyword search
            results = await self.search_tool.keyword_search(
                query=query,
                top_k=self.settings.search_top_k,
                category=category_filter,
            )

        # Build reasoning explanation
        reasoning_parts = [
            f"Performed {'hybrid' if embedding else 'keyword'} search",
            f"for query: '{query[:30]}...'",
        ]
        if category_filter:
            reasoning_parts.append(f"filtered by category: {category_filter.value}")
        reasoning_parts.append(f"Found {len(results)} results")

        if results:
            reasoning_parts.append(
                f"Top result: '{results[0].title}' (score: {results[0].relevance_score:.2f})"
            )

        reasoning = ". ".join(reasoning_parts) + "."

        logger.info(f"RetrieveAgent found {len(results)} results")

        return AgentResult(
            output=results,
            reasoning=reasoning,
            tools_used=self.tools_used,
        )
