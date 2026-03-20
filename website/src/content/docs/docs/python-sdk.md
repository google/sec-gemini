---
title: Python SDK
description: Python SDK guide
tableOfContents: true
---

The Sec-Gemini Python SDK is the primary interface for integrating **Sec-Gemini v3** into your applications. It provides a high-level, `asyncio`-native client for managing agent sessions, streaming prompts, and securely handling multi-turn tool usages.

:::tip
**Show, don't tell!** For an interactive walkthrough of the Python SDK in action, view our [Sec-Gemini v3 Colab demo](./colabs.md) or check out the generic [demo.py file](https://github.com/placeholder-demo.py).
:::

## Core Concepts

The SDK revolves around three main components: **Client**, **Session**, and **Message Stream**.

### 1. SecGemini Client
The SDK entry point. It manages authentication and connection pooling.

```python
from sec_gemini import SecGemini

client = SecGemini(api_key="...")
await client.start()
# ... use client ...
await client.close()
```

### 2. Session
A `Session` represents a persistent conversation with the agent. You can start new sessions or even resume previous ones dynamically, as the state is preserved across process restarts.

- **Creation**: `session = await client.sessions.create()`
- **Resumption**: `sessions = await client.sessions.list()` (to list and load existing ones)

### 3. Message Stream
Instead of waiting for a monolithic response, the `Session` exposes an asynchronous `session.messages.stream()` method that yields `Message` objects. This streaming-centric design allows you to build real-time monitoring and reporting UI for everything the agent is doing over the long timeframe it's working.

**Message Types:**

:::note[Alpha Notice]
These message types are subject to change as the SDK is currently in an alpha version. Additionally, please note that **not all of these messages will be received over the stream**—some are used internally for state serialization or client-to-server communication.
:::

| Category | Type | Description |
| :--- | :--- | :--- |
| **Core** | `PROMPT` | The user's input. |
| | `RESPONSE` | The agent's final answer. |
| | `FAILURE` | The agent's job failed. The workflow stops. |
| **Reasoning** | `THOUGHT` | Internal monologue/planning. |
| | `PROGRESS` | Transient updates (e.g., "Scanning...", "Planning..."). |
| **Tools** | `TOOL_CALL` | Agent execution of a tool. |
| | `TOOL_RESULT` | Output from a tool execution. |
| **Intervention** | `TOOL_CONFIRMATION_REQUEST` | Agent paused; waiting for user approval. |
| | `TOOL_CONFIRMATION_RESPONSE` | User's decision to a confirmation request. |
| | `CLARIFICATION_REQUEST` | Agent paused; needs information. |
| | `CLARIFICATION_RESPONSE` | User's answer. |
| **State Sync** | `TASK_LIST` | Full dump of the internal task hierarchy and status. |
| | `MEMORY_STATE` | Full dump of shared context and facts. |
| | `SESSION_NAME` | The generated name for this session. |
| | `SKILL_LOADED` | Notification that a skill was dynamically loaded. |
| **System** | `LOG`, `DEBUG`, `WARNING`, `ERROR` | Diagnostic information. |
| | `NOTIFICATION` | User-facing system notifications. |

## Interaction Patterns

### Basic Prompting
Start a new prompt and iterate over the generated messages.

```python
session = await client.sessions.create()
await session.prompt("Perform a security evaluation of the email configuration for example.com")

async for msg in session.messages.stream():
    # Check msg.message_type if you want to filter specific events
    print(msg)
```

### Tool Confirmation (Human-in-the-Loop)

:::note[Alpha Notice]
While the SDK fully supports programmatic tool confirmations, this feature is currently disabled on the platform in this alpha version.
:::

Sec-Gemini supports strict "Human-in-the-Loop" security. If an agent tries to use a sensitive tool (e.g., launching an intensive network scan via `nmap`), the stream pauses and emits a confirmation request.

1. **Detect Request**: Listen for the `MESSAGE_TYPE_TOOL_CONFIRMATION_REQUEST` message type.
2. **Review Intended Action**: Use `await session.confirmations.get_info()` to see exactly which tool and parameters are being requested.
3. **Approve or Deny**: Reply with `await session.confirmations.send_tool_confirmation(action_id, True/False)`.
4. **Resume Stream**: The execution resumes seamlessly based on the confirmation!

:::note
Tool confirmations persist with the session state. If you disconnect while waiting for a confirmation, the prompt will be re-emitted if you reconnect to the session via its ID.
:::

### File Context Management
You can securely supply files for the agent to refer directly to in your session.

- `await session.files.upload("path/to/local/file.txt")`
- `await session.files.list()`
- `await session.files.delete("filename.txt")`

### Skills Management
Skills are custom YAML-based capabilities you can upload to expand the agent's workflows.

- `await client.skills.list()`
- `await client.skills.upload(name="my_skill.yaml", content="...")`
- `await client.skills.delete("my_skill.yaml")`

### MCP Servers
MCP servers allow you to extend the agent's capabilities with external tools. You manage them at both the client and session levels.

- **User MCPs**: `await client.mcps.add(...)` / `await client.mcps.remove(id)`
- **Session MCPs**: `await session.mcps.set(["mcp-id-1", ...])`

:::caution
Files uploaded to a session have a **retention period of 7 days**. They will be automatically scrubbed from the storage backend following this period.
:::

## Resilience and State
The SDK is designed to be highly reliable. Agent logic executes securely server-side (in Cloud Run), and the Python client acts as a resilient subscriber:

- **Disconnect/Reconnect Compatibility**: If your local Python process exits or loses its network connection, the agent continues progressing on the server. Simply reconnecting to the same `Session` ID and calling `stream_messages()` will replay missed messages and seamlessly catch your state up to the active execution.
