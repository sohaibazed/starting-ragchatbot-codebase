# Testing Framework Enhancements

Note: this task was scoped to backend test infrastructure; no frontend code
was modified. This file documents the changes per the `/implement-feature`
command template.

## Changes

### `pyproject.toml`
- Added `httpx` to `dev` dependencies (required by FastAPI's `TestClient`).
- Added `[tool.pytest.ini_options]`:
  - `testpaths = ["backend/tests"]` and `pythonpath = ["backend"]` so tests
    resolve imports without per-file `sys.path` hacks.
  - `addopts = ["-ra", "--strict-markers", "--tb=short"]`.
  - Declared `integration` marker for tests that need `chroma_db`.
  - Muted noisy `DeprecationWarning` / `PendingDeprecationWarning`.

### `backend/tests/conftest.py` (replaced)
Shared fixtures:
- `sample_sources`, `sample_course_analytics` — canned response data.
- `mock_rag_system` — `MagicMock` RAGSystem stub with `query`,
  `get_course_analytics`, and `session_manager.create_session` pre-wired.
- `test_app` — inline FastAPI app that mirrors the `/api/query`,
  `/api/courses`, and `/` endpoints from `backend/app.py`. Defined inline
  (not imported from `app.py`) to avoid the static-files mount on
  `../frontend` and the real `RAGSystem` init that happens at import time.
- `client` — `TestClient` bound to `test_app`.

### `backend/tests/test_api_endpoints.py` (new)
Nine tests covering:
- `POST /api/query`: auto-create session, reuse existing session, source
  shape, missing field → 422, RAG failure → 500, empty-string query.
- `GET /api/courses`: analytics payload, failure → 500.
- `GET /`: root health response.

## Running

```bash
uv sync
uv run pytest backend/tests/test_api_endpoints.py -v
```

Result: 9 passed.
