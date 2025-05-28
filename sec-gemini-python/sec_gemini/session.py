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

import mimetypes
import asyncio
import logging
import random
from typing import AsyncIterator
from pathlib import Path
from base64 import b64encode

import websockets
from rich.console import Console
from rich.tree import Tree
from .constants import DEFAULT_TTL
from .enums import _EndPoints

from .http import NetworkClient

from .models.attachment import Attachment
from .models.enums import MimeType, FeedbackType, MessageType, State, Role
from .models.feedback import Feedback
from .models.message import Message, MessageType
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
        self._session: PublicSession = None  # session object

    @property
    def id(self) -> str:
        """Session ID"""
        self._refresh_data()
        return self._session.id

    @property
    def model(self) -> ModelInfo:
        """Session model"""
        self._refresh_data()
        return self._session.model

    @property
    def ttl(self) -> int:
        """Session TTL"""
        self._refresh_data()
        return self._session.ttl

    @property
    def language(self) -> str:
        """Session language"""
        self._refresh_data()
        return self._session.language

    @property
    def turns(self) -> int:
        """Session turns"""
        self._refresh_data()
        return self._session.turns

    @property
    def name(self) -> str:
        """Session name"""
        self._refresh_data()
        return self._session.name

    @property
    def description(self) -> str:
        """Session description"""
        self._refresh_data()
        return self._session.description

    @property
    def create_time(self) -> int:
        """Session creation time"""
        self._refresh_data()
        return self._session.create_time

    @property
    def update_time(self) -> int:
        """Session update time"""
        self._refresh_data()
        return self._session.update_time

    @property
    def messages(self) -> list[Message]:
        """Session messages"""
        self._refresh_data()
        return self._session.messages

    @property
    def usage(self) -> Usage:
        """Session usage"""
        self._refresh_data()
        return self._session.usage

    @property
    def can_log(self) -> bool:
        """Session can log"""
        self._refresh_data()
        return self._session.can_log

    @property
    def state(self) -> State:
        """Session state"""
        self._refresh_data()
        return self._session.state

    @property
    def files(self) -> list[PublicSessionFile]:
        """Session attachments"""
        self._refresh_data()
        return self._session.files

    def _refresh_data(self) -> PublicSession:
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

    def attach_file_from_disk(self, file_path: str) -> bool:
        """Attach a file to the session"""
        fpath = Path(file_path)
        if not fpath.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        if not fpath.is_file():
            raise ValueError(f"Path {file_path} is not a file")

        with open(file_path, "rb") as f:
            content = f.read()

        return self.attach_file(fpath.name, content)

    def delete_file(self, filename: str) -> bool:
        """Delete a file from the session"""

        # check if the file exists
        if not filename:
            raise ValueError("Filename is required")
        if not any(f.filename == filename for f in self.files):
            raise ValueError(f"File {filename} not found in session")

        # delete the file
        resp = self.http.post(
            _EndPoints.DELETE_FILE.value,
            Attachment(
                session_id=self._session.id,
                filename=filename,
                mime_type=MimeType.TEXT,
                content="",
            ),
        )
        if not resp.ok:
            logging.error("[Session][Delete][HTTP]: %s", resp.error_message)
            return False
        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Delete][Session]: %s", resp.status_message)
            return False
        return True

    def attach_file(self, filename: str, content: bytes) -> bool:
        """Attach a file to the session"""
        # guess the mime type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            raise ValueError(f"Could not determine mime type for {filename}")

        try:
            mime_type_enum = MimeType(mime_type)
        except ValueError:
            raise ValueError(f"Mime type {mime_type} not supported")

        # we always encode the content to base64
        content = b64encode(content).decode("ascii")

        # generate a unique id for the attachment
        attachment = Attachment(
            session_id=self._session.id,
            filename=filename,
            mime_type=mime_type_enum,
            content=content,
        )

        resp = self.http.post(_EndPoints.ATTACH_FILE.value, attachment)
        if not resp.ok:
            logging.error("[Session][Attachment][HTTP]: %s", resp.error_message)
            return False
        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Attachment][Session]: %s", resp.status_message)
            return False
        return True

    def send_bug_report(self, bug: str, group_id: str = "") -> bool:
        """Send a bug report"""
        feedback = Feedback(
            session_id=self._session.id,
            type=FeedbackType.BUG_REPORT,
            score=0,
            comment=bug,
        )
        if group_id:
            feedback.group_id = group_id

        return self._upload_feedback(feedback)

    def send_feedback(self, score: int, comment: str, group_id: str = "") -> bool:
        """Send session/span feedback"""
        feedback = Feedback(
            session_id=self._session.id,
            type=FeedbackType.USER_FEEDBACK,
            score=score,
            comment=comment,
        )
        if group_id:
            feedback.group_id = group_id

        return self._upload_feedback(feedback)

    def _upload_feedback(self, feedback: Feedback) -> bool:
        """Send feedback to the server"""

        resp = self.http.post(_EndPoints.SEND_FEEDBACK.value, feedback)
        if not resp.ok:
            logging.error("[Session][Feedback][HTTP]: %s", resp.error_message)
            return False
        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Feedback][Session]: %s", resp.status_message)
            return False
        return True

    def update(self, name: str = "", description: str = "", ttl: int = 0) -> bool:
        """Update session information"""

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
        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Update][Session]: %s", resp.status_message)
            return False
        return True

    def delete(self) -> bool:
        """Delete the session"""
        resp = self.http.post(_EndPoints.DELETE_SESSION.value, self._session)
        if not resp.ok:
            logging.error("[Session][Delete][HTTP]: %s", resp.error_message)
            return False
        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Delete][Session]: %s", resp.status_message)
            return False
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
                prefix = f"[{msg.role}][{msg.message_type}]"
                if msg.message_type == MessageType.RESULT:
                    text = f"{prefix}[green]\n{msg.get_content()}[/green]"
                elif msg.message_type == MessageType.INFO:
                    text = f"{prefix}[blue]\n{msg.get_content()}[/blue]"
                else:
                    text = f"[grey]{prefix}{msg.get_content()}[grey]"
            else:
                # FIXME more info here
                text = f"[{msg.role}][{msg.message_type}][magenta][File]{msg.mime_type}File[/magenta]"

            tree_data[msg.id] = tree_data[msg.parent_id].add(text)

        console.print(tree_data["3713"])

    def register(
        self,
        model: ModelInfo,
        ttl: int = DEFAULT_TTL,
        name: str = "",
        description: str = "",
        language: str = "en",
    ) -> bool:
        """Initializes the session

        notes:
         - usually called via `SecGemini.create_session()`
        """
        # FIXME: add model customization

        # basic checks
        if ttl < 300:
            raise ValueError("TTL must be greater than 300 seconds")

        # generate a friendly name if not provided
        if not name:
            name = self._generate_session_name()

        # register the session
        session = PublicSession(
            model=model,
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

        resp = OpResult(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error("[Session][Register][Session]: %s", resp.status_message)
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
            logging.error("[Sesssion][Generate][HTTP]: %s", resp.error_message)
            return None

        resp = SessionResponse(**resp.data)
        if resp.status_code != ResponseStatus.OK:
            logging.error(
                "[Session][Generate][Response] %d:%s",
                resp.status_code,
                resp.status_message,
            )
            return None
        return resp

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
                            data = await ws.recv()
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
            logging.error("[Session][Resume][HTTP]: %s", resp.error_message)
            return None

        try:
            session = PublicSession(**resp.data)
        except Exception as e:
            logging.error("[Session][Resume][Session]: %s - %s", repr(e), resp.data)
            return None
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
