"""Shared pytest fixtures for the RAG system tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def sample_sources():
    """A couple of source citations as the API returns them."""
    return [
        {"text": "Course A - Lesson 1", "url": "https://example.com/a/1"},
        {"text": "Course B - Lesson 3", "url": None},
    ]


@pytest.fixture
def sample_course_analytics():
    return {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }


@pytest.fixture
def mock_rag_system(sample_sources, sample_course_analytics):
    """A RAGSystem test double with query + analytics + session_manager stubbed."""
    rag = MagicMock()
    rag.session_manager = MagicMock()
    rag.session_manager.create_session.return_value = "test-session-123"
    rag.query.return_value = ("This is a test answer.", sample_sources)
    rag.get_course_analytics.return_value = sample_course_analytics
    return rag


@pytest.fixture
def test_app(mock_rag_system):
    """Standalone FastAPI app mirroring backend/app.py endpoints.

    Defined inline to avoid importing backend/app.py (which mounts static
    files from ../frontend and triggers a real RAGSystem init on import).
    """
    app = FastAPI(title="Course Materials RAG System (test)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class SourceItem(BaseModel):
        text: str
        url: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[SourceItem]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {"status": "ok", "service": "Course Materials RAG System"}

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)
