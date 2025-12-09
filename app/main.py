"""CivicNav FastAPI application.

City services Q&A API with agentic RAG pipeline.
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agents.query_agent import QueryAgent
from app.agents.retrieve_agent import RetrieveAgent
from app.agents.answer_agent import AnswerAgent
from app.config import get_settings
from app.models.schemas import (
    Category,
    CategoryInfo,
    CategoriesResponse,
    Citation,
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    IntentClassification,
    OverallHealth,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    ServiceHealth,
    ServicesStatus,
)
from app.tools.openai_tool import get_openai_tool
from app.tools.search_tool import get_search_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("CivicNav starting up...")
    settings = get_settings()
    if settings.is_configured:
        logger.info("Azure services configured")
    else:
        logger.warning("Azure services not fully configured - running in limited mode")
    yield
    logger.info("CivicNav shutting down...")


# Create FastAPI app
app = FastAPI(
    title="CivicNav API",
    description="City services Q&A API with agentic RAG pipeline",
    version=get_settings().app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An internal error occurred. Please try again later.",
        ).model_dump(),
    )


# API Endpoints


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def submit_query(request: QueryRequest) -> QueryResponse:
    """Submit a natural language query through the agentic pipeline.

    Processes a natural language question through:
    1. QueryAgent - classifies intent and extracts entities
    2. RetrieveAgent - performs hybrid search
    3. AnswerAgent - synthesizes response with citations
    """
    start_time = time.perf_counter()
    logger.info(f"Query received: {request.query[:50]}...")

    try:
        # Stage 1: Query Agent - Intent Classification
        query_agent = QueryAgent()
        query_result = await query_agent.execute(request.query)

        if query_result.output is None:
            raise HTTPException(status_code=500, detail="Query classification failed")

        intent: IntentClassification = query_result.output

        # Stage 2: Retrieve Agent - Hybrid Search
        retrieve_agent = RetrieveAgent()
        retrieve_result = await retrieve_agent.execute((request.query, intent))

        search_results = retrieve_result.output or []

        # Stage 3: Answer Agent - Response Synthesis
        answer_agent = AnswerAgent()
        answer_result = await answer_agent.execute((request.query, search_results, intent))

        if answer_result.output is None:
            raise HTTPException(status_code=500, detail="Answer synthesis failed")

        answer_data = answer_result.output

        # Calculate total latency
        total_latency = (time.perf_counter() - start_time) * 1000

        # Build response
        response = QueryResponse(
            id=uuid4(),
            answer=answer_data["answer"],
            citations=[
                Citation(**c) if isinstance(c, dict) else c
                for c in answer_data.get("citations", [])
            ],
            intent=intent,
            reasoning=f"{query_result.reasoning} | {retrieve_result.reasoning} | {answer_result.reasoning}",
            latency_ms=total_latency,
        )

        logger.info(f"Query completed in {total_latency:.0f}ms")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_knowledge_base(request: SearchRequest) -> SearchResponse:
    """Perform direct search without running the full agentic pipeline.

    Returns raw search results for the given query.
    """
    logger.info(f"Search request: {request.query[:50]}...")

    try:
        search_tool = get_search_tool()

        # Use keyword search for direct search endpoint
        results = await search_tool.keyword_search(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
        )

        return SearchResponse(
            results=results,
            total_count=len(results),
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories", response_model=CategoriesResponse, tags=["Categories"])
async def list_categories() -> CategoriesResponse:
    """List all available service categories with entry counts."""
    logger.info("Categories request")

    try:
        search_tool = get_search_tool()
        category_counts = await search_tool.get_categories()

        categories = [
            CategoryInfo(name=name, count=count)
            for name, count in category_counts.items()
        ]

        return CategoriesResponse(categories=categories)

    except Exception as e:
        logger.error(f"Categories request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/feedback",
    response_model=FeedbackResponse,
    status_code=201,
    tags=["Feedback"],
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Submit feedback on an answer for quality improvement."""
    logger.info(f"Feedback received for answer {request.answer_id}: rating={request.rating}")

    # In a production system, this would store feedback in a database
    # For the lab, we just acknowledge receipt
    return FeedbackResponse(
        id=uuid4(),
        status="received",
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check service health status."""
    settings = get_settings()

    # Check service connections
    services = ServicesStatus()

    try:
        openai_tool = get_openai_tool()
        if await openai_tool.check_connection():
            services.openai = ServiceHealth.CONNECTED
    except Exception as e:
        logger.warning(f"OpenAI health check failed: {e}")

    try:
        search_tool = get_search_tool()
        if await search_tool.check_connection():
            services.search = ServiceHealth.CONNECTED
    except Exception as e:
        logger.warning(f"Search health check failed: {e}")

    # Determine overall health
    if services.openai == ServiceHealth.CONNECTED and services.search == ServiceHealth.CONNECTED:
        status = OverallHealth.HEALTHY
    elif services.openai == ServiceHealth.CONNECTED or services.search == ServiceHealth.CONNECTED:
        status = OverallHealth.DEGRADED
    else:
        status = OverallHealth.UNHEALTHY

    return HealthResponse(
        status=status,
        version=settings.app_version,
        services=services,
    )


# Mount static files for chat UI
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
