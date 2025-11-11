# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interactive session class that interact with the user."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import traceback
from base64 import b64encode
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any

import httpx
import websockets
from mcp.server.fastmcp.tools import Tool
from rich.console import Console
from rich.tree import Tree
from tqdm import tqdm

from .constants import DEFAULT_TTL
from .enums import _EndPoints
from .http import NetworkClient
from .logger import get_logger
from .models.attachment import Attachment
from .models.detach_file_request import DetachFileRequest
from .models.enums import FeedbackType, MessageType, MimeType, Role, State
from .models.feedback import Feedback
from .models.local_tool import LocalTool
from .models.message import Message
from .models.modelinfo import ModelInfo
from .models.opresult import OpResult, ResponseStatus
from .models.public import (
  PublicLogsTable,
  PublicSession,
  PublicSessionFile,
  PublicUser,
)
from .models.session_request import SessionRequest
from .models.session_response import SessionResponse
from .models.usage import Usage
from .utils import generate_session_name

DEBUG = False

log = get_logger()


class InteractiveSession:
  """Interactive session with Sec-Gemini"""

  def __init__(
    self,
    user: PublicUser,
    base_url: str,
    base_websockets_url: str,
    api_key: str,
    enable_logging: bool = True,
    logs_processor_api_url: str | None = None,
  ):
    self.user = user
    self.base_url = base_url
    self.websocket_url = base_websockets_url
    self.api_key = api_key
    self.enable_logging = enable_logging
    if logs_processor_api_url is None:
      self.logs_processor_api_url = os.environ.get(
        "SEC_GEMINI_LOGS_PROCESSOR_API_URL"
      )
    else:
      self.logs_processor_api_url = logs_processor_api_url

    self.http = NetworkClient(self.base_url, self.api_key)
    self._session: PublicSession | None = None  # session object
    self._local_tool_definitions: list[LocalTool] = []
    self._local_tool_functions: dict[str, Callable[..., Any]] = {}

  @property
  def id(self) -> str:
    """Session ID"""
    assert self._session is not None
    return self._session.id

  @property
  def model(self) -> ModelInfo:
    """Session model"""
    assert self._session is not None
    self._refresh_data()
    return self._session.model

  @property
  def ttl(self) -> int:
    """Session TTL"""
    assert self._session is not None
    self._refresh_data()
    return self._session.ttl

  @property
  def language(self) -> str:
    """Session language"""
    assert self._session is not None
    self._refresh_data()
    return self._session.language

  @property
  def turns(self) -> int:
    """Session turns"""
    assert self._session is not None
    self._refresh_data()
    return self._session.turns

  @property
  def name(self) -> str:
    """Session name"""
    assert self._session is not None
    self._refresh_data()
    return self._session.name

  @property
  def description(self) -> str:
    """Session description"""
    assert self._session is not None
    self._refresh_data()
    return self._session.description

  @property
  def create_time(self) -> float:
    """Session creation time"""
    assert self._session is not None
    self._refresh_data()
    return self._session.create_time

  @property
  def update_time(self) -> float:
    """Session update time"""
    assert self._session is not None
    self._refresh_data()
    return self._session.update_time

  @property
  def messages(self) -> list[Message]:
    """Session messages"""
    assert self._session is not None
    self._refresh_data()
    return self._session.messages

  @property
  def usage(self) -> Usage:
    """Session usage"""
    assert self._session is not None
    self._refresh_data()
    return self._session.usage

  @property
  def can_log(self) -> bool:
    """Session can log"""
    assert self._session is not None
    self._refresh_data()
    return self._session.can_log

  @property
  def state(self) -> State:
    """Session state"""
    assert self._session is not None
    self._refresh_data()
    return self._session.state

  @property
  def files(self) -> list[PublicSessionFile]:
    """Session attachments"""
    assert self._session is not None
    self._refresh_data()
    return self._session.files

  @property
  def logs_table(self) -> PublicLogsTable | None:
    """Session logs table, if any"""
    assert self._session is not None
    self._refresh_data()
    return self._session.logs_table

  def _refresh_data(self) -> None:
    """Refresh the session"""
    if self._session is None:
      raise ValueError("Session not initialized")
    self._session = self.fetch_session(self._session.id)

  def resume(self, session_id: str) -> bool:
    """Resume existing session"""
    session = self.fetch_session(session_id)
    if session is not None:
      self._session = session
      log.info(
        "[Session][Resume]: Session {%s} (%s) resumed",
        session.id,
        session.name,
      )
      return True
    log.error("[Session][Resume]: Session %s not found", session_id)
    return False

  def attach_file_from_disk(self, file_path: str) -> PublicSessionFile | None:
    """Attach a file to the session from disk. Returns a PublicSessionFile with the
    information, or None in case of errors.
    """
    fpath = Path(file_path)
    if not fpath.exists():
      raise FileNotFoundError(f"File {file_path} not found")
    if not fpath.is_file():
      raise ValueError(f"Path {file_path} is not a file")

    content = fpath.read_bytes()

    return self.attach_file(fpath.name, content)

  def attach_file(
    self, filename: str, content: bytes, mime_type_hint: str | None = None
  ) -> PublicSessionFile | None:
    """Attach a file to the session. Returns a PublicSessionFile with the
    information, or None in case of errors.
    """
    assert self._session is not None

    # we always encode the content to base64
    encoded_content = b64encode(content).decode("ascii")

    # generate a unique id for the attachment
    attachment = Attachment(
      session_id=self._session.id,
      filename=filename,
      mime_type=mime_type_hint,
      content=encoded_content,
    )

    resp = self.http.post(_EndPoints.ATTACH_FILE.value, attachment)
    if not resp.ok:
      log.error(f"[Session][AttachFile][HTTP]: {resp.error_message}")
      return None

    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      log.error(f"[Session][AttachFile][Session]: {op_result.status_message}")
      return None

    if op_result.data is None:
      log.error("[Session][AttachFile][Session]: op_result.data is None")
      return None

    try:
      public_session_file = PublicSessionFile(**op_result.data)
    except Exception:
      log.error(
        f"Exception when parsing PublicSessionFile. {traceback.format_exc()}"
      )
      return None

    msg = f"[Session][AttachFile] session_id={self._session.id} {public_session_file.sha256}: OK"
    log.debug(msg)

    return public_session_file

  def detach_file(self, file_idx: int) -> bool:
    """Detach a file from the session. The file to detach is indicated by
    its index in the `session.files` list.
    """
    resp = self.http.post(
      f"{_EndPoints.DETACH_FILE.value}",
      DetachFileRequest(
        session_id=self.id,
        file_idx=file_idx,
      ),
    )
    if not resp.ok:
      error_msg = f"[Session][DetachFile][HTTP]: {resp.error_message}"
      log.error(error_msg)
      return False

    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      error_msg = f"[Session][DetachFile][HTTP]: {op_result.status_message}"
      log.error(error_msg)
      return False

    msg = f"[Session][DetachFile] session_id={self.id}, {file_idx=}: OK"
    log.debug(msg)
    return True

  def attach_logs(
    self,
    logs_hash: str,
  ) -> bool:
    """Attach logs to the session. Returns True if success, False otherwise."""
    assert self._session is not None

    client = httpx.Client()
    params = {
      "session_id": self.id,
      "logs_hash": logs_hash,
    }
    headers = {
      "x-api-key": self.api_key,
    }

    url = f"{self.http.base_url.rstrip('/')}{_EndPoints.ATTACH_LOGS.value}"
    resp = client.post(url, params=params, headers=headers)
    if resp.status_code != 200:
      log.error(
        f"[Session][AttachLogs][HTTP]: {resp.status_code} {resp.content.decode('utf-8')}"
      )
      return False

    msg = (
      f"[Session][AttachLogs] session_id={self._session.id} {logs_hash=}: OK"
    )
    log.debug(msg)

    return True

  def send_bug_report(self, bug: str, group_id: str = "") -> bool:
    """Send a bug report"""
    assert self._session is not None
    feedback = Feedback(
      session_id=self._session.id,
      group_id=group_id,
      type=FeedbackType.BUG_REPORT,
      score=0,
      comment=bug,
    )
    return self._upload_feedback(feedback)

  def send_feedback(self, score: int, comment: str, group_id: str = "") -> bool:
    """Send session/span feedback"""
    assert self._session is not None
    feedback = Feedback(
      session_id=self._session.id,
      group_id=group_id,
      type=FeedbackType.USER_FEEDBACK,
      score=score,
      comment=comment,
    )
    return self._upload_feedback(feedback)

  def _upload_feedback(self, feedback: Feedback) -> bool:
    """Send feedback to the server"""
    resp = self.http.post(_EndPoints.SEND_FEEDBACK.value, feedback)
    if not resp.ok:
      log.error(f"[Session][Feedback][HTTP]: {resp.error_message}")
      return False

    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      log.error(f"[Session][Feedback][Session]: {op_result.status_message}")
      return False
    return True

  def update(self, name: str = "", description: str = "", ttl: int = 0) -> bool:
    """Update session information"""
    assert self._session is not None

    # update the session object
    if name:
      self._session.name = name

    if description:
      self._session.description = description

    if ttl:
      if ttl < 300:
        raise ValueError("TTL must be greater than 300 seconds")
      self._session.ttl = ttl

    resp = self.http.post(_EndPoints.UPDATE_SESSION.value, self._session)
    if not resp.ok:
      log.error("[Session][Update][HTTP]: %s", resp.error_message)
      return False
    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      log.error("[Session][Update][Session]: %s", op_result.status_message)
      return False
    return True

  def delete(self) -> bool:
    """Delete the session"""
    assert self._session is not None

    resp = self.http.post(_EndPoints.DELETE_SESSION.value, self._session)
    if not resp.ok:
      log.error("[Session][Delete][HTTP]: %s", resp.error_message)
      return False

    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      log.error("[Session][Delete][Session]: %s", op_result.status_message)
      return False

    self._session = None
    return True

  def history(self) -> list[Message]:
    """Get the history of the session"""
    session = self.fetch_session(self.id)  # we pull the latest info
    if session is None:
      return []
    else:
      return session.messages

  def visualize(self) -> None:
    """Visualize the session data"""
    session = self.fetch_session(self.id)  # we pull the latest info
    if session is None:
      return
    console = Console()
    tree_data = {}

    tree_data["3713"] = Tree(
      f"[bold]{session.name}[/bold] - tokens: {session.usage.total_tokens}"
    )
    for msg in session.messages:
      if msg.mime_type == MimeType.TEXT:
        content = msg.get_content()
        assert isinstance(content, str)
        prefix = f"[{msg.role}][{msg.message_type}]"
        if msg.message_type == MessageType.RESULT:
          text = f"{prefix}[green]\n{content}[/green]"
        elif msg.message_type == MessageType.INFO:
          text = f"{prefix}[blue]\n{content}[/blue]"
        else:
          text = f"[grey]{prefix}{content}[grey]"
      else:
        # FIXME more info here
        text = f"[{msg.role}][{msg.message_type}][magenta][File]{msg.mime_type}File[/magenta]"

      tree_data[msg.id] = tree_data[msg.parent_id].add(text)

    console.print(tree_data["3713"])

  def register(
    self,
    model: str | ModelInfo,
    ttl: int = DEFAULT_TTL,
    name: str = "",
    description: str = "",
    language: str = "en",
    tools: list[Callable[..., Any]] | None = None,
    mcp_servers: list[str] | None = None,
    agents_config: dict[str, dict] | None = None,
  ) -> None:
    """Initializes the session.

    This method is usually called via `SecGemini().create_session()`, it is not
    meant to be invoked by external clients.

    Args:
    - agents_config: a key-value store, where the keys are agents' names (as
    specified in SecGeminiAgent.name), the values are dictionaries that can
    store arbitrary agent-specifc config.
    - TODO: document all other arguments.

    Raises an exception in case of errors.
    """
    # basic checks
    if ttl < 300:
      raise ValueError("TTL must be greater than 300 seconds")

    # generate a friendly name if not provided
    if not name:
      name = self._generate_session_name()

    # Parse tools
    local_tools: list[LocalTool] = []
    if tools:
      for tool in tools:
        if callable(tool):
          mcp_tool = Tool.from_function(tool)
          local_tool = LocalTool.from_dict(mcp_tool.model_dump())
          self._local_tool_functions[local_tool.name] = tool
          local_tools.append(local_tool)
          log.info(
            f"Registered local tool: {local_tool.name} - {local_tool.description}"
          )
        else:
          log.warning(
            f"Invalid tool type: {type(tool)}. Only callables are supported."
          )

    if mcp_servers:
      for server in mcp_servers:
        raise NotImplementedError(
          f"Remote tools from MCP server '{server}' are not yet supported."
        )

    if agents_config is None:
      agents_config = {}

    if isinstance(model, ModelInfo):
      model_info = model
    elif isinstance(model, str):
      model_name, version, use_experimental = ModelInfo.parse_model_string(
        model
      )
      model_info = ModelInfo(
        model_name=model_name,
        description="",
        version=version,
        use_experimental=use_experimental,
        model_string=model,
        toolsets=[],
      )
    else:
      raise ValueError(f"Invalid model as input: {model}")

    # register the session
    session = PublicSession(
      model=model_info,
      user_id=self.user.id,
      org_id=self.user.org_id,
      ttl=ttl,
      language=language,
      name=name,
      description=description,
      can_log=self.enable_logging,
      logs_table=None,
      state=State.START,
      local_tools=local_tools,
      agents_config=agents_config,
    )

    resp = self.http.post(_EndPoints.REGISTER_SESSION.value, session)
    if not resp.ok:
      log.error("[Session][Register][HTTP]: %s", resp.error_message)
      raise Exception(
        f"Error when registering the session: {resp.error_message}"
      )

    op_result = OpResult(**resp.data)
    if op_result.status_code != ResponseStatus.OK:
      log.error("[Session][Register][Session]: %s", op_result.status_message)
      raise Exception(
        f"Error when registering the session: {op_result.status_message}"
      )

    self._session = session
    log.info(
      "[Session][Register][Session]: Session %s (%s) registered",
      session.id,
      session.name,
    )

    return None

  def query(self, prompt: str) -> SessionResponse:
    """Classic AI Generation/Completion Request"""
    if not prompt:
      raise ValueError("Prompt is required")

    # build a synchronous request and return the response
    message = self._build_prompt_message(prompt)
    req = SessionRequest(
      id=self.id,
      messages=[message],
      local_tools=self._local_tool_definitions,
    )
    resp = self.http.post(_EndPoints.GENERATE.value, req)

    if not resp.ok:
      error_msg = f"[Session][Generate][HTTP]: {resp.error_message}"
      log.error(error_msg)
      raise Exception(error_msg)

    session_resp = SessionResponse(**resp.data)
    if session_resp.status_code != ResponseStatus.OK:
      error_msg = f"[Session][Generate][Response] {session_resp.status_code}:{session_resp.status_message}"
      log.error(error_msg)
      raise Exception(error_msg)

    return session_resp

  async def stream(
    self, prompt: str = "", recv_only: bool = False
  ) -> AsyncGenerator[Message, None]:
    """Initiates a robust, auto-reconnecting streaming session with the backend.

    This method handles the WebSocket connection lifecycle, including initial
    handshake, sending the user query, and yielding subsequent messages. It
    automatically attempts to reconnect if the connection is dropped unexpectedly,
    ensuring stream continuity without re-sending the initial prompt.

    Internal "local tool call" requests from the backend are handled automatically
    and are not yielded to the caller.

    Args:
      prompt: The initial user query to start the session.
      recv_only: If True, skips sending the prompt. Primarily used for
                  testing or attaching to existing sessions.

    Yields:
      Message: Message objects intended for the end user (e.g., info,
                thinking, or final results).

    Raises:
      ValueError: If the prompt is invalid.
      Exception: If streaming fails after the maximum number of retries.
    """
    if not isinstance(prompt, str):
      raise ValueError("prompt must be a string")
    if prompt == "" and not recv_only:
      raise ValueError("prompt is required")

    message = self._build_prompt_message(prompt)
    # FIXME: maybe move to http client as it is super specific
    url = f"{self.websocket_url}{_EndPoints.STREAM.value}"
    url += f"?api_key={self.api_key}&session_id={self.id}"

    # LOGIC OVERVIEW:
    # We use a nested loop structure to handle robust streaming with automatic
    # retries.
    # 1. Outer Loop (Connection Manager): Handles establishing the WebSocket
    # connection and managing retry attempts with exponential backoff if the
    # connection fails totally.
    # 2. Inner Loop (Message Stream): actively listens for messages on an open
    # connection.
    #
    # STATE FLAGS:
    # - `should_send_prompt`: Ensures we only send the user's query once, on the
    # very first successful connection. If we drop and reconnect, we resume
    # listening without re-triggering the backend.
    # - `should_reconnect`: acts as the exit signal. We keep retrying until we
    # receive an explicit 'END' signal or a non-OK status from the backend.

    log.info(f"Initiating stream for session {self.id}")

    max_retries = 5
    should_reconnect = True
    should_send_prompt = True
    for attempt in range(max_retries):
      try:
        log.debug(
          f"Before connection attempt. {should_reconnect=} {should_send_prompt=}"
        )
        async with websockets.connect(
          url,
          ping_interval=20,  # seconds
          ping_timeout=20,  # seconds
          close_timeout=60,
        ) as ws:
          log.debug("Connection succeeded!")
          if should_send_prompt and prompt != "":
            await ws.send(message.model_dump_json())
            should_send_prompt = False
            log.debug("Prompt sent!")
          else:
            log.debug(
              f"Skipped sending the prompt. {should_send_prompt=} {prompt=}"
            )

          # Receiving until a message with State=END or a status_code!=OK, or
          # until a timeout.
          try:
            log.debug("Entering recv loop")
            while True:
              data = await ws.recv(decode=True)
              msg = Message.from_json(data)
              log.debug(f"Received message {msg}")

              # Check if this message is about a tool call; if so,
              # deal with it and reply to the backend without
              # yielding the message -- it's not for the user!
              if msg.message_type == MessageType.LOCAL_TOOL_CALL:
                log.debug(f"Received tool call request: {msg.get_content()!r}")
                tool_output_message = self._execute_tool(msg)
                log.debug(
                  f"Sending tool output message: {tool_output_message.get_content()!r}"
                )
                await ws.send(tool_output_message.model_dump_json())
                # We do NOT yield LOCAL_TOOL messages to the client
                continue

              yield msg

              # Check for error messages
              if msg.status_code != ResponseStatus.OK:
                log.error(
                  "[Session][Stream][Response] %d:%s",
                  msg.status_code,
                  msg.content,
                )
                should_reconnect = False
                break

              # Check for END messages
              if msg.state == State.END:
                log.debug(f"Got message with state END: {msg}")
                should_reconnect = False
                break

          except Exception as e:
            # Something happened, and the websocket can't be trusted anymore. We
            # log and go back at the beginning of the loop. If appropriate,
            # we'll reconnect.
            log.error("[Session][Stream][Error]: %s", repr(e))

        if should_reconnect and (attempt < max_retries):
          log.error(
            f"Connection dropped, waiting before attemptint to reconnect, attempt={attempt + 1}"
          )
          await asyncio.sleep(1 * (attempt + 1))
        else:
          break

      except Exception as e:
        log.error(f"Connection attempt {attempt + 1} failed: {e}")
        if attempt == max_retries - 1:
          raise e
        await asyncio.sleep(1 * (attempt + 1))

    if should_reconnect:
      raise Exception("Streaming failed after maximum number of retries.")

    log.info(f"Done processing stream for session {self.id}")

  def _execute_tool(self, tool_call_message: Message) -> Message:
    """Executes a tool and returns the output message."""
    tool_call = json.loads(tool_call_message.get_content())

    # get the tool name and args using various naming conventions
    tool_name = tool_call.get("tool_name", "")
    if not tool_name:
      tool_name = tool_call.get("name", "")

    tool_args = tool_call.get("tool_args", {})
    if not tool_args:
      tool_args = tool_call.get("args", {})

    tool_function = self._local_tool_functions.get(tool_name)
    if not tool_function:
      msg = f"Tool '{tool_name}' not found."
      log.warning(msg)
      error_message = Message(
        role=Role.USER,
        message_type=MessageType.LOCAL_TOOL_RESULT,
        mime_type=MimeType.SERIALIZED_JSON,
        status_code=ResponseStatus.INTERNAL_ERROR,
        content=json.dumps(
          {"name": tool_name, "output": msg, "is_error": True}
        ),
      )

      return error_message
    try:
      dmegs = f"Executing tool '{tool_name}' with args: {tool_args}"
      log.info(dmegs)
      tool_output = str(tool_function(**tool_args))
      output_message = Message(
        role=Role.USER,
        message_type=MessageType.LOCAL_TOOL_RESULT,
        mime_type=MimeType.SERIALIZED_JSON,
      )
      output_message.set_content(
        json.dumps({"name": tool_name, "output": tool_output})
      )
      return output_message
    except Exception as e:
      msg = f"Tool '{tool_name}' execution failed: {e}"
      log.warning(msg)
      error_message = Message(
        role=Role.USER,
        message_type=MessageType.LOCAL_TOOL_RESULT,
        mime_type=MimeType.SERIALIZED_JSON,
        status_code=ResponseStatus.INTERNAL_ERROR,
        content=msg,
      )
      return error_message

  def fetch_session(self, id: str) -> PublicSession:
    """Get the full session from the server"""
    # for security reason, the api requires the user_id and org_id
    query_params = {"session_id": id}
    resp = self.http.get(
      f"{_EndPoints.GET_SESSION.value}", query_params=query_params
    )
    if not resp.ok:
      error_msg = f"[Session][Resume][HTTP]: {resp.error_message}"
      log.error(error_msg)
      raise Exception(error_msg)

    try:
      session = PublicSession(**resp.data)
    except Exception as e:
      error_msg = f"[Session][Resume][Session]: {e!r} - {resp.data}"
      log.error(error_msg)
      raise Exception(error_msg)
    return session

  def _build_prompt_message(self, prompt: str) -> Message:
    message = Message(
      role=Role.USER,
      state=State.QUERY,
      message_type=MessageType.QUERY,
      mime_type=MimeType.TEXT,
    )
    return message.set_content(prompt)

  def _generate_session_name(self) -> str:
    """Generates a unique  cybersecurity session themed name."""
    return generate_session_name()

  def upload_and_attach_logs(
    self, jsonl_path: Path, custom_fields_mapping: dict[str, str] | None = None
  ) -> None:
    """Uploads a JSONL log file and attaches it to the current session.

    This method reads a log file where each line is a valid JSON object
    (JSONL format), uploads it to create a new data table, and then
    associates that table with the current analysis session for querying.

    Args:
        jsonl_path (Path): The local file system path to the JSONL log file
            to be uploaded.
        custom_fields_mapping (dict[str, str] | None): An optional
            dictionary to rename fields from the source log file to new
            destination names in the resulting table. The dictionary must be
            in the format `{'destination_field': 'source_field'}`. For
            example, `{'id': '_id'}` would rename the `_id` field
            from the JSONL file to `id` in the table. If None, no
            fields are renamed. Defaults to None.

    Returns:
        None
    """
    if self.logs_processor_api_url is None:
      log.error(
        "Logs processor API URL required: explictly pass it or set env"
        " variable SEC_GEMINI_LOGS_PROCESSOR_API_URL (e.g., in .env)."
      )
      sys.exit(1)

    try:
      logs_hash = _compute_file_hash(jsonl_path)
      log.info(f"Computed info for {jsonl_path}: {logs_hash=}")

      # Upload logs
      # TODO: can we write this around the existing NetworkClient, without
      # using httpx directly.
      with httpx.Client() as client:
        params: dict[str, Any] = {
          "logs_hash": logs_hash,
          "can_log": self.can_log,
        }
        headers = {
          "x-api-key": self.api_key,
        }

        log.info(f"Creating logs table {logs_hash=} and {self.can_log=}")
        response = client.post(
          f"{self.logs_processor_api_url}/create_logs_table",
          params=params,
          headers=headers,
          timeout=None,
        )
        # Raise an exception for 4xx/5xx responses
        response.raise_for_status()

        try:
          response_content = response.json()
          if response_content.get("table_created", False) is True:
            # Table was just created, let's proceed with the uploads.
            upload_logs = True
          else:
            upload_logs = False
            log.warning(
              f"Skipping upload as the table already existed: {response_content}"
            )
        except json.JSONDecodeError:
          log.error(f"ERROR: Could not parse response as JSON: {response}")
          return

        inserted_log_lines = 0
        if upload_logs:
          # Read the file in chunks, extract lines (without parsing each
          # individual line), and upload them to the logs processor
          # backend.
          unused_buffer = ""
          for chunk in _read_file_chunks_with_progress_bar(
            jsonl_path, chunk_size=10_000_000
          ):
            log_lines, unused_buffer = parse_chunk(chunk, unused_buffer)

            if len(log_lines) == 0:
              assert unused_buffer == ""
              # Nothing else to process
              continue

            log.info(
              f"Uploading {len(log_lines)} log lines with {logs_hash=} and {self.can_log=}"
            )

            payload: dict[str, Any] = {
              "logs_hash": logs_hash,
              "can_log": self.can_log,
              "log_lines": log_lines,
            }
            if custom_fields_mapping:
              payload["custom_fields_mapping"] = custom_fields_mapping
            response = client.post(
              f"{self.logs_processor_api_url}/upload_logs",
              json=payload,
              headers=headers,
              timeout=None,
            )

            # Raise an exception for 4xx/5xx responses
            response.raise_for_status()

            response_content = response.json()

            inserted_log_lines += response_content.get("inserted_log_lines", 0)
          log.info(
            f"\nUpload complete! Inserted a total of {inserted_log_lines} log lines."
          )

      # Attach logs to session
      res = self.attach_logs(logs_hash)
      if res is False:
        raise Exception("Error when attach logs to session")

    except httpx.HTTPStatusError as exc:
      # An HTTP error occurred (e.g., 404 Not Found, 500 Server Error)
      log.error(
        f"HTTP Error: {exc.response.status_code} while requesting {exc.request.url!r}."
      )
      try:
        error_details = exc.response.json()
        log.error(f"Server error message: {error_details}")
      except json.JSONDecodeError:
        log.error(f"Could not parse response as JSON: {exc.response}")
        return

    except httpx.RequestError as e:
      log.error(
        f"An error occurred while requesting {e.request.url!r}. Error details: {e}"
      )

    except Exception as e:
      log.error(f"An unexpected error occurred: {e}. {traceback.format_exc()}")

  def __copy__(self) -> InteractiveSession:
    int_sess = InteractiveSession(
      user=self.user.model_copy(),
      base_url=self.base_url,
      base_websockets_url=self.websocket_url,
      api_key=self.api_key,
      enable_logging=self.enable_logging,
    )
    if self._session is not None:
      int_sess._session = self._session.model_copy()
    return int_sess

  def __str__(self) -> str:
    return f"<InteractiveSession(id={self.id})>"


def _compute_file_hash(file_path: Path) -> str:
  log.debug("Computing file hash...")
  hasher = hashlib.blake2s(key=b"secgemini")
  with file_path.open("rb") as f:
    while chunk := f.read(4096):
      hasher.update(chunk)
  file_hash = hasher.hexdigest()
  log.debug(f"File hash: {file_hash}")
  return file_hash


def _read_file_chunks_with_progress_bar(
  file_path: Path, chunk_size: int = 4096
):
  """
  Read file chunks, with a progress bar.
  """
  total = file_path.stat().st_size
  with tqdm(
    ascii=True, unit_scale=True, unit="B", unit_divisor=1024, total=total
  ) as bar:
    with file_path.open("rb") as f:
      while data := f.read(chunk_size):
        yield data
        bar.update(len(data))


def parse_chunk(chunk: bytes, unused_buffer: str) -> tuple[list[str], str]:
  data = unused_buffer + chunk.decode("utf-8")
  lines: list[str] = data.splitlines(keepends=True)

  if len(lines) == 0:
    return [], ""

  # The last line might be incomplete, so we save it for the next chunk
  last_line = lines[-1]
  if len(last_line) > 0 and last_line[-1] != "\n":
    unused_buffer = lines.pop()
  else:
    unused_buffer = ""

  return lines, unused_buffer
