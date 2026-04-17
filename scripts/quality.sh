#!/usr/bin/env bash
set -euo pipefail

# Run all code quality checks
cd "$(dirname "$0")/.."

echo "==> Running code quality checks"

echo ""
echo "[1/2] Format check (black)"
uv run black --check backend/ main.py

echo ""
echo "[2/2] Tests (pytest)"
uv run pytest backend/ || {
    echo "Tests failed or none found"
    exit 1
}

echo ""
echo "All quality checks passed."
