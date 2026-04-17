# Code Quality Tooling Changes

Note: this task was backend/tooling rather than frontend, but logging here per the `/implement-feature` template.

## Summary

Added `black` as the project's Python code formatter and created shell scripts for running quality checks.

## Files changed

### `pyproject.toml`
- Added `black>=24.0.0` to the `dev` dependency group.
- Added `[tool.black]` config: `line-length = 100`, `target-version = ["py313"]`, excludes `.venv` and `backend/chroma_db`.

### `scripts/format.sh` (new)
- Runs `uv run black backend/ main.py` to auto-format all Python code.

### `scripts/lint.sh` (new)
- Runs `uv run black --check --diff backend/ main.py`. Non-zero exit on unformatted code — suitable for CI.

### `scripts/quality.sh` (new)
- Runs format check + `pytest backend/` as a single gate.

All scripts use `set -euo pipefail` and `cd` to the repo root so they work from any CWD.

## Codebase formatting pass

Ran `./scripts/format.sh` once to normalize the existing code. 12 files reformatted across `backend/` (including `backend/tests/`). After the pass, `./scripts/lint.sh` reports clean.

## Usage

```bash
./scripts/format.sh    # auto-format
./scripts/lint.sh      # check only (CI)
./scripts/quality.sh   # format check + tests
```

## Design notes

- Chose `black` only (no ruff/isort) to match the "simple, minimal, no over-engineering" preference. Easy to add later if needed.
- Line length 100 (not black's default 88) to reduce churn on the existing codebase and keep long Anthropic API call sites readable.
- Dev-only dependency — not installed in production containers.
