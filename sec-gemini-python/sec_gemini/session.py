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
import logging
import os
import random
import sys
import traceback
from base64 import b64encode
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import httpx
import websockets
from rich.console import Console
from rich.tree import Tree
from tqdm import tqdm

from .constants import DEFAULT_TTL
from .enums import _EndPoints
from .http import NetworkClient
from .models.attachment import Attachment
from .models.detach_file_request import DetachFileRequest
from .models.enums import FeedbackType, MessageType, MimeType, Role, State
from .models.feedback import Feedback
from .models.message import Message
from .models.modelinfo import ModelInfo
from .models.opresult import OpResult, ResponseStatus
from .models.public import PublicLogsTable, PublicSession, PublicSessionFile, PublicUser
from .models.session_request import SessionRequest
from .models.session_response import SessionResponse
from .models.usage import Usage

DEBUG = False


class InteractiveSession:
    "Interactive session with Sec-Gemini"

    def __init__(
        self,
        user: PublicUser,
        base_url: str,
        base_websockets_url: str,
        api_key: str,
        enable_logging: bool = True,
    ):
        self.user = user
        self.base_url = base_url
        self.websocket_url = base_websockets_url
        self.api_key = api_key
        self.enable_logging = enable_logging
        self.http = NetworkClient(self.base_url, self.api_key)
        self._session: Optional[PublicSession] = None  # session object

    @property
    def id(self) -> str:
        """Session ID"""
        assert self._session is not None
        self._refresh_data()
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
        "Resume existing session"
        session = self.fetch_session(session_id)
        if session is not None:
            self._session = session
            logging.info(
                "[Session][Resume]: Session {%s} (%s) resumed", session.id, session.name
            )
            return True
        logging.error("[Session][Resume]: Session %s not found", session_id)
        return False

    def attach_file_from_disk(self, file_path: str) -> Optional[PublicSessionFile]:
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
        self, filename: str, content: bytes, mime_type_hint: Optional[str] = None
    ) -> Optional[PublicSessionFile]:
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
            logging.error(f"[Session][AttachFile][HTTP]: {resp.error_message}")
            return None

        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            logging.error(f"[Session][AttachFile][Session]: {op_result.status_message}")
            return None

        if op_result.data is None:
            logging.error("[Session][AttachFile][Session]: op_result.data is None")
            return None

        try:
            public_session_file = PublicSessionFile(**op_result.data)
        except Exception:
            logging.error(
                f"Exception when parsing PublicSessionFile. {traceback.format_exc()}"
            )
            return None

        msg = f"[Session][AttachFile] session_id={self._session.id} {public_session_file.sha256}: OK"
        logging.debug(msg)

        return public_session_file

    def detach_file(self, session_id: str, file_idx: int) -> bool:
        """Detach a file from the session. The file to detach is indicated by
        its index in the `session.files` list.
        """

        resp = self.http.post(
            f"{_EndPoints.DETACH_FILE.value}",
            DetachFileRequest(
                session_id=session_id,
                file_idx=file_idx,
            ),
        )
        if not resp.ok:
            error_msg = f"[Session][DetachFile][HTTP]: {resp.error_message}"
            logging.error(error_msg)
            return False

        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            error_msg = f"[Session][DetachFile][HTTP]: {op_result.status_message}"
            logging.error(error_msg)
            return False

        msg = f"[Session][DetachFile] {session_id=} {file_idx=}: OK"
        logging.debug(msg)
        return True

    def _attach_logs(
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

        url = f"{self.http.base_url.rstrip('/')}{_EndPoints.ATTACH_LOGS.value}"
        resp = client.post(url, params=params)
        if resp.status_code != 200:
            logging.error(
                f"[Session][AttachLogs][HTTP]: {resp.status_code} {resp.content.decode('utf-8')}"
            )
            return False

        msg = f"[Session][AttachLogs] session_id={self._session.id} {logs_hash=}: OK"
        logging.debug(msg)

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
            logging.error(f"[Session][Feedback][HTTP]: {resp.error_message}")
            return False

        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            logging.error(f"[Session][Feedback][Session]: {op_result.status_message}")
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
            logging.error("[Session][Update][HTTP]: %s", resp.error_message)
            return False
        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            logging.error("[Session][Update][Session]: %s", op_result.status_message)
            return False
        return True

    def delete(self) -> bool:
        """Delete the session"""
        assert self._session is not None

        resp = self.http.post(_EndPoints.DELETE_SESSION.value, self._session)
        if not resp.ok:
            logging.error("[Session][Delete][HTTP]: %s", resp.error_message)
            return False

        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            logging.error("[Session][Delete][Session]: %s", op_result.status_message)
            return False

        self._session = None
        return True

    def history(self) -> list[Message]:
        "Get the history of the session"
        session = self.fetch_session(self.id)  # we pull the latest info
        if session is None:
            return []
        else:
            return session.messages

    def visualize(self) -> None:
        "Visualize the session data"
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
    ) -> bool:
        """Initializes the session

        notes:
         - usually called via `SecGemini.create_session()`
        """

        # basic checks
        if ttl < 300:
            raise ValueError("TTL must be greater than 300 seconds")

        # generate a friendly name if not provided
        if not name:
            name = self._generate_session_name()

        if isinstance(model, ModelInfo):
            model_info = model
        elif isinstance(model, str):
            model_info = ModelInfo.get_model_info_from_model_string(model)
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
        )

        resp = self.http.post(_EndPoints.REGISTER_SESSION.value, session)
        if not resp.ok:
            logging.error("[Session][Register][HTTP]: %s", resp.error_message)
            return False

        op_result = OpResult(**resp.data)
        if op_result.status_code != ResponseStatus.OK:
            logging.error("[Session][Register][Session]: %s", op_result.status_message)
            return False

        self._session = session
        logging.info(
            "[Session][Register][Session]: Session %s (%s) registered",
            session.id,
            session.name,
        )

        return True

    def query(self, prompt: str) -> SessionResponse:
        """Classic AI Generation/Completion Request"""
        if not prompt:
            raise ValueError("Prompt is required")

        # build a synchronous request and return the response
        message = self._build_prompt_message(prompt)
        req = SessionRequest(id=self.id, messages=[message])
        resp = self.http.post(_EndPoints.GENERATE.value, req)

        if not resp.ok:
            error_msg = f"[Session][Generate][HTTP]: {resp.error_message}"
            logging.error(error_msg)
            raise Exception(error_msg)

        session_resp = SessionResponse(**resp.data)
        if session_resp.status_code != ResponseStatus.OK:
            error_msg = f"[Session][Generate][Response] {session_resp.status_code}:{session_resp.status_message}"
            logging.error(error_msg)
            raise Exception(error_msg)
        return session_resp

    async def stream(self, prompt: str) -> AsyncIterator[Message]:
        """Streaming Generation/Completion Request"""
        if not prompt:
            raise ValueError("query is required")

        message = self._build_prompt_message(prompt)
        # FIXME: maybe move to http client as it is super specific
        url = f"{self.websocket_url}{_EndPoints.STREAM.value}"
        url += f"?api_key={self.api_key}&session_id={self.id}"
        max_retries = 5
        for attempt in range(max_retries):
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,  # seconds
                    ping_timeout=20,  # seconds
                    close_timeout=60,
                ) as ws:
                    # send request
                    await ws.send(message.model_dump_json())

                    # receiving til end
                    while True:
                        try:
                            data = await ws.recv(decode=True)
                            msg = Message.from_json(data)
                            if msg.status_code != ResponseStatus.OK:
                                logging.error(
                                    "[Session][Stream][Response] %d:%s",
                                    msg.status_code,
                                    msg.status_message,
                                )
                                break
                            yield msg
                        except Exception as e:
                            logging.error("[Session][Stream][Error]: %s", repr(e))
                            break
            except Exception as e:
                logging.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

    def fetch_session(self, id: str) -> PublicSession:
        """Get the full session from the server"""
        # for security reason, the api requires the user_id and org_id
        query_params = {"session_id": id}
        resp = self.http.get(
            f"{_EndPoints.GET_SESSION.value}", query_params=query_params
        )
        if not resp.ok:
            error_msg = f"[Session][Resume][HTTP]: {resp.error_message}"
            logging.error(error_msg)
            raise Exception(error_msg)

        try:
            session = PublicSession(**resp.data)
        except Exception as e:
            error_msg = f"[Session][Resume][Session]: {e!r} - {resp.data}"
            logging.error(error_msg)
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

        terms = [
            "firewall",
            "xss",
            "sql-injection",
            "csrf",
            "dos",
            "botnet",
            "rsa",
            "aes",
            "sha",
            "hmac",
            "xtea",
            "twofish",
            "serpent",
            "dh",
            "ecc",
            "dsa",
            "pgp",
            "vpn",
            "tor",
            "dns",
            "tls",
            "ssl",
            "https",
            "ssh",
            "sftp",
            "snmp",
            "ldap",
            "kerberos",
            "oauth",
            "bcrypt",
            "scrypt",
            "argon2",
            "pbkdf2",
            "ransomware",
            "trojan",
            "rootkit",
            "keylogger",
            "adware",
            "spyware",
            "worm",
            "virus",
            "antivirus",
            "sandbox",
            "ids",
            "ips",
            "honeybot",
            "honeypot",
            "siem",
            "nids",
            "hids",
            "waf",
            "dast",
            "sast",
            "vulnerability",
            "exploit",
            "0day",
            "logjam",
            "heartbleed",
            "shellshock",
            "poodle",
            "spectre",
            "meltdown",
            "rowhammer",
            "sca",
            "padding",
            "oracle",
        ]

        adjs = [
            "beautiful",
            "creative",
            "dangerous",
            "elegant",
            "fancy",
            "gorgeous",
            "handsome",
            "intelligent",
            "jolly",
            "kind",
            "lovely",
            "magnificent",
            "nice",
            "outstanding",
            "perfect",
            "quick",
            "reliable",
            "smart",
            "talented",
            "unique",
            "vibrant",
            "wonderful",
            "young",
            "zany",
            "amazing",
            "brave",
            "calm",
            "delightful",
            "eager",
            "faithful",
            "gentle",
            "happy",
            "incredible",
            "jovial",
            "keen",
            "lucky",
            "merry",
            "nice",
            "optimistic",
            "proud",
            "quiet",
            "reliable",
            "scary",
            "thoughtful",
            "upbeat",
            "victorious",
            "witty",
            "zealous",
            "adorable",
            "brilliant",
            "charming",
            "daring",
            "eager",
            "fearless",
            "graceful",
            "honest",
            "intelligent",
            "jolly",
            "kind",
            "lively",
            "modest",
            "nice",
            "optimistic",
            "proud",
            "quiet",
            "reliable",
            "silly",
            "thoughtful",
            "upbeat",
            "victorious",
            "witty",
        ]

        return f"{random.choice(adjs)}-{random.choice(terms)}"

    def upload_and_attach_logs(self, jsonl_path: Path) -> None:
        # TODO: write this code around the existing NetworkClient, without using
        # httpx directly.

        SEC_GEMINI_LOGS_PROCESSOR_API_URL = os.environ.get(
            "SEC_GEMINI_LOGS_PROCESSOR_API_URL"
        )
        if SEC_GEMINI_LOGS_PROCESSOR_API_URL is None:
            print(
                "ERROR: set the SEC_GEMINI_LOGS_PROCESSOR_API_URL environment variable"
            )
            sys.exit(1)

        try:
            logs_hash = _compute_file_hash(jsonl_path)
            print(f"Computed info for {jsonl_path}: {logs_hash=}")

            # Upload logs
            with httpx.Client() as client:
                params: dict[str, Any] = {
                    "logs_hash": logs_hash,
                    "can_log": self.can_log,
                }
                headers = {
                    "x-api-key": self.api_key,
                }

                print(f"Creating logs table {logs_hash=} and {self.can_log=}")
                response = client.post(
                    f"{SEC_GEMINI_LOGS_PROCESSOR_API_URL}/create_logs_table",
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
                        print(
                            f"Skipping upload as the table already existed: {response_content}"
                        )
                except json.JSONDecodeError:
                    print(f"ERROR: Could not parse response as JSON: {response}")
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
                        if len(log_lines) > 0:
                            if DEBUG:
                                print(
                                    f"Uploading {len(log_lines)} log lines with {logs_hash=} and {self.can_log=}"
                                )

                            payload: dict[str, Any] = {
                                "logs_hash": logs_hash,
                                "can_log": self.can_log,
                                "log_lines": log_lines,
                            }
                            response = client.post(
                                f"{SEC_GEMINI_LOGS_PROCESSOR_API_URL}/upload_logs",
                                json=payload,
                                headers=headers,
                                timeout=None,
                            )

                        # Raise an exception for 4xx/5xx responses
                        response.raise_for_status()

                        response_content = response.json()

                        inserted_log_lines += response_content.get(
                            "inserted_log_lines", 0
                        )
                    print(
                        f"\nUpload complete! Inserted a total of {inserted_log_lines} log lines."
                    )

            # Attach logs to session
            res = self._attach_logs(logs_hash)
            if res is False:
                raise Exception("Error when attach logs to session")

        except httpx.HTTPStatusError as exc:
            # An HTTP error occurred (e.g., 404 Not Found, 500 Server Error)
            print(
                f"HTTP Error: {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            try:
                error_details = exc.response.json()
                print(f"Server error message: {error_details}")
            except json.JSONDecodeError:
                print(f"ERROR: Could not parse response as JSON: {exc.response}")
                return

        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}.")
            print(f"Error details: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}. {traceback.format_exc()}")

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


def _compute_file_hash(file_path: Path) -> str:
    print("Computing file hash...")
    hasher = hashlib.blake2s(key=b"secgemini")
    with file_path.open("rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_file_chunks_with_progress_bar(file_path: Path, chunk_size: int = 4096):
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
