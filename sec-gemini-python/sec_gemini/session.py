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
import logging
import random
import traceback
from base64 import b64encode
from pathlib import Path
from typing import AsyncIterator, Optional

import websockets
from rich.console import Console
from rich.tree import Tree

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
from .models.public import PublicSession, PublicSessionFile, PublicUser
from .models.session_request import SessionRequest
from .models.session_response import SessionResponse
from .models.usage import Usage


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

    def attach_file(self, filename: str, content: bytes) -> Optional[PublicSessionFile]:
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

    async def stream(self, query: str) -> AsyncIterator[Message]:
        """Streaming Generation/Completion Request"""
        if not query:
            raise ValueError("query is required")

        message = self._build_prompt_message(query)
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
