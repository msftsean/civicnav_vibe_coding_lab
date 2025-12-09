"""CivicNav agents for the agentic RAG pipeline.

This package contains the three-stage agent pipeline:
- QueryAgent: Intent classification and entity extraction
- RetrieveAgent: Hybrid search with vector + keyword + semantic ranking
- AnswerAgent: Response synthesis with citations
"""

from app.agents.base import BaseAgent

__all__ = ["BaseAgent"]
