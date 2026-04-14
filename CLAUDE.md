# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) chatbot that answers questions about course materials. Uses ChromaDB for vector storage, Anthropic Claude for AI generation, and FastAPI for the backend with a vanilla HTML/JS/CSS frontend.

## Commands

```bash
# Install dependencies
uv sync

# Run the application (starts uvicorn on port 8000)
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Architecture

The app runs from `backend/` with FastAPI serving both the API and the static frontend.

**Request flow:** Frontend → `POST /api/query` → `RAGSystem.query()` → Claude calls `search_course_content` tool → `VectorStore.search()` → ChromaDB → results returned to Claude → response sent to frontend.

### Backend Components (`backend/`)

- **`app.py`** — FastAPI app. Mounts frontend as static files at `/`. Loads documents from `../docs/` on startup. Two endpoints: `POST /api/query` and `GET /api/courses`.
- **`rag_system.py`** — Orchestrator. Wires together all components and handles the query pipeline.
- **`vector_store.py`** — ChromaDB wrapper with two collections: `course_catalog` (course metadata, title-based lookup) and `course_content` (chunked lesson text). Course titles serve as unique IDs.
- **`document_processor.py`** — Parses course text files with a specific format (header lines for title/link/instructor, then `Lesson N:` markers). Chunks text by sentences with configurable overlap.
- **`ai_generator.py`** — Anthropic API client. Handles tool use loop: sends query → if Claude requests tool use → executes tool → sends results back for final response.
- **`search_tools.py`** — Tool abstraction layer. `Tool` ABC + `CourseSearchTool` (wraps VectorStore.search) + `ToolManager` (registry, execution, source tracking). The tool is exposed to Claude via Anthropic's tool calling API.
- **`session_manager.py`** — In-memory conversation history per session. Keeps last N exchanges for multi-turn context.
- **`models.py`** — Pydantic models: `Course`, `Lesson`, `CourseChunk`.
- **`config.py`** — Dataclass config loaded from env vars. Key settings: chunk size (800), overlap (100), max results (5), model (`claude-sonnet-4-20250514`), embedding model (`all-MiniLM-L6-v2`).

### Frontend (`frontend/`)

Vanilla HTML/JS/CSS chat interface. Communicates with backend via fetch to `/api/query`.

### Document Format (`docs/`)

Course text files follow a strict format:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <lesson title>
Lesson Link: <url>
<lesson content...>
```

## Key Design Decisions

- ChromaDB persists to `backend/chroma_db/` — this directory is auto-created and gitignored
- Claude is given a `search_course_content` tool and decides when to search vs answer from general knowledge
- Course name resolution uses vector similarity search against the catalog collection, so partial/fuzzy course names work
- The server runs from `backend/` directory, so all relative paths in backend code are relative to `backend/`
- No test suite exists currently

## Environment

- Python 3.13, managed with `uv`
- Requires `ANTHROPIC_API_KEY` in `.env` at project root (see `.env.example`)
