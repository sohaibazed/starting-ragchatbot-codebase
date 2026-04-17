"""Integration-style tests for RAGSystem.query() focused on content queries.

These stub out AIGenerator (no network) but use the real VectorStore against
the on-disk chroma_db so we exercise tool registration, tool execution, and
source wiring end-to-end.
"""

from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from config import config  # noqa: E402
from rag_system import RAGSystem  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (BACKEND / "chroma_db").exists(),
    reason="chroma_db not populated; run the server once to ingest docs",
)


@pytest.fixture
def rag():
    # Run from backend dir so relative CHROMA_PATH resolves
    cwd = os.getcwd()
    os.chdir(BACKEND)
    try:
        yield RAGSystem(config)
    finally:
        os.chdir(cwd)


def test_search_tool_is_registered(rag):
    defs = rag.tool_manager.get_tool_definitions()
    names = {d["name"] for d in defs}
    assert "search_course_content" in names


def test_both_tools_registered(rag):
    defs = rag.tool_manager.get_tool_definitions()
    names = {d["name"] for d in defs}
    assert {"search_course_content", "get_course_outline"}.issubset(names)


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live-model smoke test",
)
def test_real_query_end_to_end(rag):
    """Hit the real Anthropic API against real chroma. Reproduces the prod bug if present."""
    answer, sources = rag.query("What is MCP?")
    assert isinstance(answer, str) and answer.strip(), f"empty answer: {answer!r}"


def test_content_query_routes_through_search_tool(rag):
    """Simulate Claude deciding to call search_course_content."""
    with patch.object(rag.ai_generator, "generate_response") as mock_gen:

        def fake_generate(query, conversation_history=None, tools=None, tool_manager=None):
            # Ensure tools were provided
            assert tools is not None
            names = {t["name"] for t in tools}
            assert "search_course_content" in names
            # Manually invoke the search tool as Claude would
            result = tool_manager.execute_tool("search_course_content", query="MCP architecture")
            assert "No relevant content found" not in result
            assert result  # non-empty
            return "stubbed answer"

        mock_gen.side_effect = fake_generate
        answer, sources = rag.query("What does lesson 2 of MCP teach?")

    assert answer == "stubbed answer"
    # Sources should be populated from the tool's last_sources
    assert len(sources) > 0
    assert all("text" in s and "url" in s for s in sources)


def test_search_tool_returns_content_for_known_course(rag):
    """Direct tool execution against the real vector store."""
    out = rag.search_tool.execute(query="architecture", course_name="MCP")
    assert "No relevant content found" not in out
    assert "No course found" not in out
    assert len(rag.search_tool.last_sources) > 0


@pytest.mark.xfail(
    reason="Known quality issue: _resolve_course_name has no similarity threshold, "
    "so any string maps to nearest course. Separate from the 'query failed' bug."
)
def test_search_tool_handles_unknown_course(rag):
    out = rag.search_tool.execute(query="x", course_name="NONEXISTENT_XYZ_999")
    assert "No course found" in out


def test_sources_reset_after_query(rag):
    with patch.object(rag.ai_generator, "generate_response") as mock_gen:

        def fake_generate(query, conversation_history=None, tools=None, tool_manager=None):
            tool_manager.execute_tool("search_course_content", query="MCP")
            return "ok"

        mock_gen.side_effect = fake_generate
        rag.query("q")

    assert rag.tool_manager.get_last_sources() == []
