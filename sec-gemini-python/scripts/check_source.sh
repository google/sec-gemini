#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SEC_GEMINI_PYTHON_DIR="$(readlink -f "$SCRIPT_DIR/..")"

cd $SEC_GEMINI_PYTHON_DIR

set -xe

# Check if we have unformatted files
uv run ruff format --check

# Check if we have linter warnings (fix with `uv run ruff check --fix`)
uv run ruff check

# Check if we have typing issues
uv run mypy sec_gemini tests scripts/*.py
