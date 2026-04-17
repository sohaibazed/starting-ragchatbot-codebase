#!/usr/bin/env bash
set -euo pipefail

# Check Python formatting without modifying files
cd "$(dirname "$0")/.."
echo "==> Checking Python formatting (black --check)"
uv run black --check --diff backend/ main.py
