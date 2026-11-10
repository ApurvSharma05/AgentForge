"""
FastAPI Serving Layer for AgentForge Multi-Agent Research System.
Exposes REST endpoints for health checks and research pipeline execution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from config import Config
from pipeline import Pipeline

app = FastAPI(
    title="AgentForge API",
    description="Multi-Agent Automated Research and Report Generation Pipeline API",
    version="1.0.0"
)

_pipeline: Optional[Pipeline] = None


def get_pipeline() -> Pipeline:
    """Lazy-initialization singleton for the Pipeline orchestrator."""
    global _pipeline
    if _pipeline is None:
        try:
            config = Config()
            _pipeline = Pipeline(config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize AgentForge pipeline: {str(e)}"
            )
    return _pipeline


class ResearchRequest(BaseModel):
    """Input payload for research execution."""
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic to investigate")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of search results to fetch")
    max_pages: int = Field(default=3, ge=1, le=10, description="Maximum web pages to scrape and read")


class ResearchResponse(BaseModel):
    """Output response containing research report and evaluation."""
    success: bool
    topic: str
    final_report: Optional[str] = None
    critique_feedback: Optional[str] = None
    is_approved: Optional[bool] = None
    critique_score: Optional[int] = None
    critique_failed: bool = False
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    timestamp: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness and readiness health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/research", response_model=ResearchResponse)
def run_research(req: ResearchRequest, response: Response) -> ResearchResponse:
    """
    Execute the 4-agent research pipeline on a user query.
    1. SearchAgent: Query Google via SerpAPI
    2. ReaderAgent: Scrape clean page content
    3. WriterAgent: Synthesize in-depth report via Groq LLM
    4. CritiqueAgent: Review and evaluate report quality

    Status codes:
    - 200 and success=true: report written and critique completed.
    - 200 and success=false, critique_failed=true: report is returned but the critique failed
      (see `error` and `warnings`).
    - 502 and success=false: no report (search, read or write stage failed). The body has the
      same shape, with `error` set.
    - 500: pipeline could not start or an unexpected exception escaped.
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.execute(
            topic=req.topic,
            num_search_results=req.num_results,
            max_pages_to_read=req.max_pages,
            save_results=False,
        )

        body = ResearchResponse(
            success=result["success"],
            topic=result["topic"],
            final_report=result.get("final_report"),
            critique_feedback=result.get("critique_feedback"),
            is_approved=result.get("is_approved"),
            critique_score=result.get("critique_score"),
            critique_failed=result.get("critique_failed", False),
            warnings=result.get("warnings") or [],
            error=result.get("error"),
            timestamp=result["timestamp"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research pipeline execution encountered an error: {str(e)}"
        )

    if not body.success and not body.final_report:
        response.status_code = status.HTTP_502_BAD_GATEWAY
    return body
