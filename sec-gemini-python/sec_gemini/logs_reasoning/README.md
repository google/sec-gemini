# Usage

The client must provide a `LogStore` implementation with `describe_logs()` and
`search_logs()` functions implemented. See code in `logstore.py`. Once this is
done, the client can invoke sec-gemini with the LogStore-specific tools as
follows.

```py
# Initialize LogStore object.
logstore = MyLogStoreImplementation(...)

# Make the tools required for the logs reasoning agent.
session_tools = logstore.make_tools()

sg = SecGemini(...)
# Disabling session logging ensures CAT-0 compliance.
session = sg.create_session(
  tools=session_tools, model=LOGS_ANALYSIS_AGENT, enable_logging=False)

async for message in session.stream(PROMPT):
  # process outputs and results here
```

See example sqlite-backed implementation of the `LogStore` in
`sec-gemini-python/sec_gemini/logs_reasoning/sqlite_backend/sqlite.py`
and subsequent usage of it in `sec-gemini-python/scripts/logs_reasoning_local_search.py`.
