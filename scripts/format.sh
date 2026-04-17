#!/usr/bin/env bash
set -euo pipefail

# Format all Python code with black
cd "$(dirname "$0")/.."
echo "==> Formatting Python code with black"
uv run black backend/ main.py
