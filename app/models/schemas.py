"""Pydantic models for CivicNav entities.

This module defines all data models used throughout the CivicNav application,
including knowledge base entries, queries, search results, and agent outputs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """Service categories for city services."""

    SCHEDULE = "schedule"
    EVENT = "event"
    REPORT = "report"
    PERMIT = "permit"
    EMERGENCY = "emergency"
    GENERAL = "general"


class EntityType(str, Enum):
    """Types of entities that can be extracted from queries."""

    DATE = "date"
    LOCATION = "location"
    SERVICE_TYPE = "service_type"
    DEPARTMENT = "department"


class Entity(BaseModel):
    """An extracted entity from a user query."""

    type: EntityType
    value: str
    start_pos: int | None = None
    end_pos: int | None = None


class KnowledgeBaseEntry(BaseModel):
    """A unit of city services information stored in Azure AI Search."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=50, max_length=10000)
    category: Category
    service_type: str
    department: str
    updated_date: datetime

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty or whitespace-only")
        return v

    @field_validator("updated_date")
    @classmethod
    def date_not_future(cls, v: datetime) -> datetime:
        if v > datetime.now():
            raise ValueError("updated_date cannot be in the future")
        return v


class UserQuery(BaseModel):
    """A natural language question submitted by a user."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(..., min_length=3, max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str | None = None

    @field_validator("text")
    @classmethod
    def text_not_only_special_chars(cls, v: str) -> str:
        if not any(c.isalnum() for c in v):
            raise ValueError("text must not contain only special characters")
        return v


class IntentClassification(BaseModel):
    """Result of intent classification by QueryAgent."""

    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: list[Entity] = Field(default_factory=list)

    @property
    def is_low_confidence(self) -> bool:
        """Check if classification confidence is below threshold."""
        return self.confidence < 0.5


class SearchResult(BaseModel):
    """A single result from Azure AI Search."""

    id: str
    entry_id: str
    title: str
    content: str
    category: Category
    service_type: str | None = None
    department: str | None = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    highlight: str | None = None


class Citation(BaseModel):
    """A source reference included in system responses."""

    entry_id: str
    title: str
    snippet: str


class AgentResult(BaseModel):
    """Structured output from any agent in the pipeline."""

    output: Any
    reasoning: str
    tools_used: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class ChatMessage(BaseModel):
    """A message in the chat interface."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    sender: Literal["user", "system"]
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    reasoning: str | None = None


# API Request/Response Models


class QueryRequest(BaseModel):
    """Request body for POST /api/query."""

    query: str = Field(..., min_length=3, max_length=1000)
    session_id: UUID | None = None


class QueryResponse(BaseModel):
    """Response body for POST /api/query."""

    id: UUID
    answer: str
    citations: list[Citation]
    intent: IntentClassification
    reasoning: str | None = None
    latency_ms: float


class SearchRequest(BaseModel):
    """Request body for POST /api/search."""

    query: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    category: Category | None = None


class SearchResponse(BaseModel):
    """Response body for POST /api/search."""

    results: list[SearchResult]
    total_count: int


class CategoryInfo(BaseModel):
    """Information about a service category."""

    name: str
    count: int


class CategoriesResponse(BaseModel):
    """Response body for GET /api/categories."""

    categories: list[CategoryInfo]


class FeedbackRequest(BaseModel):
    """Request body for POST /api/feedback."""

    answer_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    """Response body for POST /api/feedback."""

    id: UUID
    status: Literal["received"] = "received"


class ServiceHealth(str, Enum):
    """Health status for individual services."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class OverallHealth(str, Enum):
    """Overall health status for the application."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServicesStatus(BaseModel):
    """Status of connected services."""

    openai: ServiceHealth = ServiceHealth.DISCONNECTED
    search: ServiceHealth = ServiceHealth.DISCONNECTED


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: OverallHealth
    version: str
    services: ServicesStatus | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] | None = None
