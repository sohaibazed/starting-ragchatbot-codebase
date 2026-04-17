"""API endpoint tests using a TestClient against an inline FastAPI app.

The inline app (see conftest.py::test_app) mirrors backend/app.py's endpoints
but omits the static-file mount at "/" so tests don't require the frontend
directory or a real RAGSystem.
"""


def test_query_creates_session_when_none_provided(client, mock_rag_system):
    resp = client.post("/api/query", json={"query": "What is MCP?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "This is a test answer."
    assert body["session_id"] == "test-session-123"
    assert len(body["sources"]) == 2
    mock_rag_system.session_manager.create_session.assert_called_once()
    mock_rag_system.query.assert_called_once_with("What is MCP?", "test-session-123")


def test_query_reuses_existing_session(client, mock_rag_system):
    resp = client.post(
        "/api/query",
        json={"query": "Follow up?", "session_id": "existing-sess"},
    )
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "existing-sess"
    mock_rag_system.session_manager.create_session.assert_not_called()
    mock_rag_system.query.assert_called_once_with("Follow up?", "existing-sess")


def test_query_source_shape(client):
    resp = client.post("/api/query", json={"query": "x"})
    sources = resp.json()["sources"]
    assert sources[0] == {"text": "Course A - Lesson 1", "url": "https://example.com/a/1"}
    assert sources[1] == {"text": "Course B - Lesson 3", "url": None}


def test_query_missing_query_field_returns_422(client):
    resp = client.post("/api/query", json={})
    assert resp.status_code == 422


def test_query_rag_failure_returns_500(client, mock_rag_system):
    mock_rag_system.query.side_effect = RuntimeError("vector store exploded")
    resp = client.post("/api/query", json={"query": "boom"})
    assert resp.status_code == 500
    assert "vector store exploded" in resp.json()["detail"]


def test_courses_returns_analytics(client, mock_rag_system):
    resp = client.get("/api/courses")
    assert resp.status_code == 200
    assert resp.json() == {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    mock_rag_system.get_course_analytics.assert_called_once()


def test_courses_failure_returns_500(client, mock_rag_system):
    mock_rag_system.get_course_analytics.side_effect = RuntimeError("db down")
    resp = client.get("/api/courses")
    assert resp.status_code == 500
    assert "db down" in resp.json()["detail"]


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_empty_string_is_accepted(client, mock_rag_system):
    resp = client.post("/api/query", json={"query": ""})
    assert resp.status_code == 200
    mock_rag_system.query.assert_called_once_with("", "test-session-123")
