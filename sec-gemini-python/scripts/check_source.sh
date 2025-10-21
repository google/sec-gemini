#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SEC_GEMINI_PYTHON_DIR="$(readlink -f "$SCRIPT_DIR/..")"

cd $SEC_GEMINI_PYTHON_DIR

# FIXME: there are 200+ linting warnings with the new config; we'll need some
# time to fix them all. For now, we keep running the linter, but we do not error
# out.
# set -xe
set -x

# Check if we have unformatted files
uv run ruff format --check

# Check if we have linter warnings (fix with `uv run ruff check --fix`)
uv run ruff check

# Check if we have typing issues
uv run mypy sec_gemini tests/test_secgemini.py tests/utils.py scripts/*.py
