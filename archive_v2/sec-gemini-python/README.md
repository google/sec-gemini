# Sec-Gemini Python SDK

## Install dependencies

```bash
uv sync --all-extras --dev
```

## Basic Usage

Set your SecGemini API key in the `SEC_GEMINI_API_KEY` environment variable (or add it to the `.env` file).

Then, see `./scripts/basic_example.py` or `./scripts/basic_openai_example.py` as examples.

You can run them with: `uv run ./scripts/basic_example.py`


# Testing

The tests mostly use mock objects. However, a few tests also expect to hit a live backend. By default such tests hit the prod backend, but the tests can be configured to hit a local backend as well.

These are the relevant environment variables:
- `SEC_GEMINI_API_KEY`: must be a valid SecGemini API key.
- `SEC_GEMINI_API_HTTP_URL`: specify a custom HTTP(s) endpoint for the API, e.g., `http://localhost:8000`.
- `SEC_GEMINI_API_WEBSOCKET_URL`: specify a custom websocket(s) endpoint for the API, e.g., `ws://localhost:8000`.

Then, to run the tests: `uv run -m pytest`.
