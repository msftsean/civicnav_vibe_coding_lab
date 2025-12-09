"""Azure AI Search tool wrapper for CivicNav.

Provides async methods for hybrid search (vector + keyword + semantic)
using Azure AI Search with DefaultAzureCredential for authentication.
"""

import logging
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery,
)

from app.config import get_settings
from app.models.schemas import Category, SearchResult

logger = logging.getLogger(__name__)


class SearchTool:
    """Wrapper for Azure AI Search operations.

    Uses DefaultAzureCredential for authentication and supports
    hybrid search combining vector, keyword, and semantic ranking.
    """

    def __init__(self) -> None:
        """Initialize the Search tool with Azure credentials."""
        self.settings = get_settings()
        self._client: SearchClient | None = None

    @property
    def client(self) -> SearchClient:
        """Get or create the SearchClient."""
        if self._client is None:
            credential = DefaultAzureCredential()
            self._client = SearchClient(
                endpoint=self.settings.azure_search_endpoint,
                index_name=self.settings.azure_search_index,
                credential=credential,
            )
        return self._client

    async def hybrid_search(
        self,
        query: str,
        vector: list[float],
        top_k: int = 5,
        category: Category | None = None,
    ) -> list[SearchResult]:
        """Perform hybrid search combining vector, keyword, and semantic ranking.

        Args:
            query: The search query text
            vector: The embedding vector for vector search
            top_k: Number of results to return
            category: Optional category filter

        Returns:
            List of SearchResult objects sorted by relevance
        """
        logger.debug(f"Hybrid search: '{query}' (top_k={top_k})")

        # Build filter if category specified
        filter_expr = f"category eq '{category.value}'" if category else None

        # Create vector query
        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )

        # Execute hybrid search with semantic ranking
        results = self.client.search(
            search_text=query,
            vector_queries=[vector_query],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="default",
            top=top_k,
            filter=filter_expr,
            select=["id", "title", "content", "category", "service_type", "department"],
            highlight_fields="content",
        )

        search_results: list[SearchResult] = []
        for result in results:
            # Get highlight if available
            highlights = result.get("@search.highlights", {})
            highlight = highlights.get("content", [""])[0] if highlights else None

            search_results.append(
                SearchResult(
                    id=result["id"],
                    entry_id=result["id"],
                    title=result["title"],
                    content=result["content"],
                    category=Category(result["category"]),
                    service_type=result.get("service_type"),
                    department=result.get("department"),
                    relevance_score=result.get("@search.score", 0.0),
                    highlight=highlight,
                )
            )

        logger.debug(f"Found {len(search_results)} results")
        return search_results

    async def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        category: Category | None = None,
    ) -> list[SearchResult]:
        """Perform keyword-only search.

        Args:
            query: The search query text
            top_k: Number of results to return
            category: Optional category filter

        Returns:
            List of SearchResult objects sorted by relevance
        """
        logger.debug(f"Keyword search: '{query}' (top_k={top_k})")

        filter_expr = f"category eq '{category.value}'" if category else None

        results = self.client.search(
            search_text=query,
            top=top_k,
            filter=filter_expr,
            select=["id", "title", "content", "category", "service_type", "department"],
            highlight_fields="content",
        )

        search_results: list[SearchResult] = []
        for result in results:
            highlights = result.get("@search.highlights", {})
            highlight = highlights.get("content", [""])[0] if highlights else None

            search_results.append(
                SearchResult(
                    id=result["id"],
                    entry_id=result["id"],
                    title=result["title"],
                    content=result["content"],
                    category=Category(result["category"]),
                    service_type=result.get("service_type"),
                    department=result.get("department"),
                    relevance_score=result.get("@search.score", 0.0),
                    highlight=highlight,
                )
            )

        return search_results

    async def get_categories(self) -> dict[str, int]:
        """Get count of entries per category.

        Returns:
            Dict mapping category name to entry count
        """
        logger.debug("Getting category counts")

        # Use faceting to get category counts
        results = self.client.search(
            search_text="*",
            top=0,
            facets=["category"],
        )

        # Extract facet counts
        category_counts: dict[str, int] = {}
        facets = results.get_facets()
        if facets and "category" in facets:
            for facet in facets["category"]:
                category_counts[facet["value"]] = facet["count"]

        return category_counts

    async def check_connection(self) -> bool:
        """Check if the Search service is accessible.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple test search
            list(self.client.search(search_text="*", top=1))
            return True
        except Exception as e:
            logger.warning(f"Search connection check failed: {e}")
            return False


# Global instance for convenience
_search_tool: SearchTool | None = None


def get_search_tool() -> SearchTool:
    """Get the global Search tool instance."""
    global _search_tool
    if _search_tool is None:
        _search_tool = SearchTool()
    return _search_tool
