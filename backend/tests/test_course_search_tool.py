"""Tests for CourseSearchTool.execute()."""

from unittest.mock import MagicMock
import pytest

from search_tools import CourseSearchTool
from vector_store import SearchResults


def make_tool(search_return):
    store = MagicMock()
    store.search.return_value = search_return
    store.get_lesson_link.return_value = "http://lesson/link"
    store.get_course_link.return_value = "http://course/link"
    return CourseSearchTool(store), store


def test_execute_returns_formatted_results_with_header():
    results = SearchResults(
        documents=["Content about MCP."],
        metadata=[{"course_title": "MCP Course", "lesson_number": 2}],
        distances=[0.1],
    )
    tool, _ = make_tool(results)
    out = tool.execute(query="what is MCP")
    assert "[MCP Course - Lesson 2]" in out
    assert "Content about MCP." in out


def test_execute_tracks_sources_with_links():
    results = SearchResults(
        documents=["doc"],
        metadata=[{"course_title": "MCP Course", "lesson_number": 3}],
        distances=[0.1],
    )
    tool, store = make_tool(results)
    tool.execute(query="q")
    assert tool.last_sources == [{"text": "MCP Course - Lesson 3", "url": "http://lesson/link"}]
    store.get_lesson_link.assert_called_once_with("MCP Course", 3)


def test_execute_empty_results_returns_friendly_message():
    tool, _ = make_tool(SearchResults(documents=[], metadata=[], distances=[]))
    out = tool.execute(query="q", course_name="X", lesson_number=9)
    assert "No relevant content found" in out
    assert "X" in out and "9" in out


def test_execute_propagates_store_error():
    tool, _ = make_tool(SearchResults.empty("Search error: boom"))
    out = tool.execute(query="q")
    assert out == "Search error: boom"


def test_execute_passes_filters_to_store():
    results = SearchResults(
        documents=["d"],
        metadata=[{"course_title": "C", "lesson_number": 1}],
        distances=[0.0],
    )
    tool, store = make_tool(results)
    tool.execute(query="q", course_name="C", lesson_number=1)
    store.search.assert_called_once_with(query="q", course_name="C", lesson_number=1)


def test_execute_returns_no_course_found_when_resolve_fails():
    """Simulate store.search returning the error path from _resolve_course_name."""
    err = SearchResults.empty("No course found matching 'Bogus'")
    tool, _ = make_tool(err)
    out = tool.execute(query="q", course_name="Bogus")
    assert "No course found matching 'Bogus'" in out


def test_execute_handles_missing_lesson_number_metadata():
    results = SearchResults(
        documents=["d"],
        metadata=[{"course_title": "C"}],
        distances=[0.0],
    )
    tool, store = make_tool(results)
    out = tool.execute(query="q")
    assert "[C]" in out
    assert tool.last_sources[0]["text"] == "C"
    assert tool.last_sources[0]["url"] == "http://course/link"
