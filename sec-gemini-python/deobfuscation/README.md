# Sec-Gemini Deobfuscation Python SDK

## Install dependencies

```bash
uv sync --all-extras --dev
```

## Basic Usage

Set your SecGemini API key in the `SEC_GEMINI_API_KEY` environment variable (or add it to the `.env` file).

Then, see `./scripts/basic_example.py` as an example.

You can run it with: `uv run ./scripts/basic_example.py`


# Testing

The tests mostly use mock objects.

Run the test with:

```bash
uv run -m pytest`
```
