from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: list[str]


@pytest.fixture
def sample_query() -> dict[str, str]:
    """A reusable, valid request body for query endpoint tests."""
    return {"query": "What does the course teach?"}


@pytest.fixture
def sample_courses() -> dict[str, object]:
    """Representative course analytics returned by the RAG system."""
    return {
        "total_courses": 2,
        "course_titles": ["Building AI Agents", "Advanced Retrieval"],
    }


@pytest.fixture
def mock_rag_system(sample_courses: dict[str, object]) -> MagicMock:
    """Mock the external RAG, vector-store, and session dependencies."""
    rag_system = MagicMock()
    rag_system.session_manager.create_session.return_value = "test-session-id"
    rag_system.query.return_value = (
        "The course teaches retrieval-augmented generation.",
        ["Building AI Agents, lesson 1"],
    )
    rag_system.get_course_analytics.return_value = sample_courses
    return rag_system


@pytest.fixture
def test_app(mock_rag_system: MagicMock) -> FastAPI:
    """Create an API-only app so tests do not require frontend static files."""
    app = FastAPI(title="Course Materials RAG System - Test")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest) -> QueryResponse:
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()

            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats() -> CourseStats:
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return "<html><body><h1>Course Materials RAG System</h1></body></html>"

    return app


@pytest.fixture
def client(test_app: FastAPI) -> Iterator[TestClient]:
    """Provide a client whose application lifecycle is managed per test."""
    with TestClient(test_app) as test_client:
        yield test_client
