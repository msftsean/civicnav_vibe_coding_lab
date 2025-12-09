"""AnswerAgent for response synthesis.

This agent synthesizes a natural language answer from search results
and generates citations for the response.
"""

import logging
from typing import Tuple

from app.agents.base import BaseAgent
from app.models.schemas import (
    AgentResult,
    Citation,
    IntentClassification,
    SearchResult,
)
from app.tools.openai_tool import get_openai_tool

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """You are a helpful city services assistant. Based on the search results provided, answer the user's question.

Guidelines:
1. Provide a clear, helpful answer based ONLY on the search results
2. If the search results don't contain relevant information, say so politely
3. Reference sources by number [1], [2], etc. when citing specific information
4. Keep the response concise but informative
5. If relevant, suggest next steps or additional resources

User Question: {query}

Search Results:
{results}

Provide a helpful answer:"""

NO_RESULTS_RESPONSE = """I don't have specific information about that in my knowledge base. Here are some suggestions:

1. Contact City Hall directly at 555-CITY (555-2489)
2. Visit the city website at www.example-city.gov
3. Try rephrasing your question with more specific terms

Is there anything else I can help you with?"""


class AnswerAgent(BaseAgent[Tuple[str, list[SearchResult], IntentClassification], dict]):
    """Agent for synthesizing answers with citations.

    Takes a tuple of (query, search_results, intent) and returns a dict
    containing the answer text and citation list.
    """

    def __init__(self) -> None:
        """Initialize the AnswerAgent."""
        super().__init__("AnswerAgent")
        self.openai_tool = get_openai_tool()

    async def run(
        self, input_data: Tuple[str, list[SearchResult], IntentClassification]
    ) -> AgentResult:
        """Synthesize an answer from search results.

        Args:
            input_data: Tuple of (query, search_results, intent)

        Returns:
            AgentResult containing dict with 'answer' and 'citations'
        """
        query, search_results, intent = input_data
        logger.info(f"AnswerAgent synthesizing answer for: {query[:50]}...")

        # Handle no results case
        if not search_results:
            logger.info("No search results, returning fallback response")
            return AgentResult(
                output={
                    "answer": NO_RESULTS_RESPONSE,
                    "citations": [],
                },
                reasoning="No relevant results found in knowledge base. Provided fallback response with contact information.",
                tools_used=self.tools_used,
            )

        # Format search results for the prompt
        results_text = self._format_results(search_results)

        # Generate answer using OpenAI
        self.use_tool("openai_chat")

        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            results=results_text,
        )

        try:
            answer = await self.openai_tool.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful city services assistant. Provide accurate, helpful answers based on the provided search results.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            # Generate citations from search results
            citations = self._generate_citations(search_results, answer)

            reasoning = f"Synthesized answer from {len(search_results)} search results. "
            reasoning += f"Generated {len(citations)} citations."

            logger.info(f"AnswerAgent generated {len(answer)} char answer with {len(citations)} citations")

            return AgentResult(
                output={
                    "answer": answer,
                    "citations": citations,
                },
                reasoning=reasoning,
                tools_used=self.tools_used,
            )

        except Exception as e:
            logger.error(f"AnswerAgent synthesis failed: {e}")
            # Return a graceful fallback
            return AgentResult(
                output={
                    "answer": "I'm having trouble generating a response right now. Please try again or contact City Hall directly.",
                    "citations": [],
                },
                reasoning=f"Synthesis failed: {e}",
                tools_used=self.tools_used,
            )

    def _format_results(self, results: list[SearchResult]) -> str:
        """Format search results for the synthesis prompt.

        Args:
            results: List of search results

        Returns:
            Formatted string of results
        """
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.content
            if len(content) > 500:
                content = content[:500] + "..."

            formatted.append(
                f"[{i}] {result.title}\n"
                f"Category: {result.category.value}\n"
                f"Content: {content}\n"
            )

        return "\n".join(formatted)

    def _generate_citations(
        self, results: list[SearchResult], answer: str
    ) -> list[Citation]:
        """Generate citations from search results.

        Args:
            results: Search results used for the answer
            answer: Generated answer text

        Returns:
            List of Citation objects
        """
        citations = []

        for i, result in enumerate(results, 1):
            # Check if this result is referenced in the answer
            # We'll include top results that might have contributed
            if i <= 3 or f"[{i}]" in answer:
                # Create a relevant snippet
                snippet = result.highlight or result.content[:150]
                if len(snippet) > 150 and not result.highlight:
                    snippet = snippet[:150] + "..."

                citations.append(
                    Citation(
                        entry_id=result.entry_id,
                        title=result.title,
                        snippet=snippet,
                    )
                )

        return citations


# Graceful fallback response generator
def generate_fallback_response(query: str, intent: IntentClassification) -> dict:
    """Generate a fallback response when the pipeline fails.

    Args:
        query: The original user query
        intent: The classified intent

    Returns:
        Dict with 'answer' and 'citations'
    """
    category_suggestions = {
        "schedule": "For schedule information, you can check the city calendar at www.example-city.gov/calendar",
        "permit": "For permit inquiries, contact the Planning Department at 555-PLAN",
        "emergency": "For emergencies, always dial 911. For non-emergencies, call 555-0100",
        "event": "For upcoming events, visit the community events page at www.example-city.gov/events",
        "report": "To report an issue, call 311 or use the city's online reporting system",
        "general": "For general inquiries, contact City Hall at 555-CITY",
    }

    suggestion = category_suggestions.get(
        intent.category.value,
        "For assistance, contact City Hall at 555-CITY"
    )

    return {
        "answer": f"I couldn't find specific information about your question. {suggestion}",
        "citations": [],
    }
