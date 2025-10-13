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
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.table import Table

from .constants import DEFAULT_TTL
from .enums import _URLS, _EndPoints
from .http import NetworkClient
from .logger import get_logger
from .models.modelinfo import ModelInfo
from .models.public import PublicSession, UserInfo
from .session import InteractiveSession

load_dotenv()

log = get_logger()


class SecGemini:
    DEFAULT_STABLE_MODEL_NAME = "sec-gemini-stable"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        base_websockets_url: Optional[str] = None,
        logs_processor_api_url: Optional[str] = None,
        console_width: int = 500,
        verbose: bool = False,
        debug: bool = False,
    ) -> None:
        """Initializes the SecGemini API client.

        Args:
            api_key: Api key used to authenticate with SecGemini. Key can also be passed
            via the environment variable SEC_GEMINI_API_KEY.

            base_url: Server base_url. Defaults to online server.

            base_websockets_url: Websockets base_url. Defaults to online server.

            console_width: Console width for displaying tables. Defaults to 500.

            verbose: enable INFO-level logs.

            debug: enable DEBUG-level logs.
        """

        if verbose:
            log.setLevel(logging.INFO)
        if debug:
            log.setLevel(logging.DEBUG)

        if base_url is None:
            base_url = os.getenv("SEC_GEMINI_API_HTTP_URL", "").strip()
            if base_url == "":
                base_url = _URLS.HTTPS.value

        if base_websockets_url is None:
            base_websockets_url = os.getenv("SEC_GEMINI_API_WEBSOCKET_URL", "").strip()
            if base_websockets_url == "":
                base_websockets_url = _URLS.WEBSOCKET.value

        # setup display console
        self.console = Console(width=console_width)

        if api_key is None:
            api_key = os.getenv("SEC_GEMINI_API_KEY", "").strip()

        if api_key == "":
            raise ValueError(
                "API key required: explictly pass it or set env variable SEC_GEMINI_API_KEY (e.g in .env)."
            )
        self.api_key = api_key

        self.logs_processor_api_url = logs_processor_api_url

        # http(s) endpoint
        self.base_url = base_url.rstrip("/")
        if not self.base_url.startswith("http"):
            raise ValueError(f'Invalid base_url "{base_url}" - must be an http(s) url.')

        # websocket endpoint
        self.base_websockets_url = base_websockets_url.rstrip("/")
        if not self.base_websockets_url.startswith("ws"):
            raise ValueError(
                f'Invalid base_websockets_url "{base_websockets_url}" - must be a ws(s) url.'
            )

        # instantiate the network client
        self.http = NetworkClient(base_url, api_key)

        # check if the API is working and get user info
        ui = self.get_user_info()
        if not ui:
            raise ValueError("API Key is invalid or the API is down.")
        self.user = ui.user

        # assign the models to stable and experimental
        self.available_models = ui.available_models
        assert len(self.available_models) > 0

    def get_user_info(self) -> UserInfo:
        """Return users info.

        Returns:
            UserInfo: User information.
        """

        response = self.http.get(_EndPoints.USER_INFO.value)
        if not response.ok:
            error_msg = f"Request Error: {response.error_message}"
            logging.error(error_msg)
            raise Exception(error_msg)

        return UserInfo(**response.data)

    def display_info(self) -> None:
        """Display users info."""
        ui = self.get_user_info()
        if not ui:
            print("Failed to retrieve user information.")
            return

        # User Table
        if ui.user.key_expire_time > 0:
            key_expire_time = datetime.fromtimestamp(ui.user.key_expire_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            key_expire_time = "Never"

        vendors = ", ".join([v.name for v in ui.user.vendors])

        user_table = Table(title="User Information", box=box.ROUNDED)
        user_table.add_column("Attribute", style="dim", width=20)
        user_table.add_column("Value")
        user_table.add_row("Type", ui.user.type.value)
        user_table.add_row("User ID", ui.user.id)
        user_table.add_row("Organization ID", ui.user.org_id)
        user_table.add_row("Never log?", str(ui.user.never_log))
        user_table.add_row("Key Expiration Time", key_expire_time)
        user_table.add_row(
            "Can disable session logging?", str(ui.user.can_disable_logging)
        )
        user_table.add_row(
            "Cam use experimental features?", str(ui.user.allow_experimental)
        )
        user_table.add_row("TPM Quota", f"{ui.user.tpm}")
        user_table.add_row("RPM Quota", f"{ui.user.rpm}")
        user_table.add_row("Vendors", vendors)
        self.console.print(user_table)

        # Model Table
        self._display_models(ui.available_models)

        # Session Table
        self._display_sessions(ui.sessions)

    def create_session(
        self,
        name: str = "",
        description: str = "",
        ttl: int = DEFAULT_TTL,
        enable_logging: bool = True,
        model: str = DEFAULT_STABLE_MODEL_NAME,
        language: str = "en",
        tools: list[Callable[..., Any]] | None = None,
        mcp_servers: list[str] | None = None,
    ) -> InteractiveSession:
        """Creates a new session.

        Args:
            name: optional session name
            description: optional session description
            ttl: live of inactive session in sec.
            enable_logging: enable/disable logging (if allowed)
            model: model to use, either a str or ModelInfo
            language: language to use - defaults to 'en'
            tools: list of functions to be available to the model.
            mcp_servers: list of MCP servers to connect to.

        Returns:
            A new session object.
        """

        session = InteractiveSession(
            user=self.user,
            base_url=self.base_url,
            base_websockets_url=self.base_websockets_url,
            api_key=self.api_key,
            enable_logging=enable_logging,
            logs_processor_api_url=self.logs_processor_api_url,
        )

        session.register(
            ttl=ttl,
            model=model,
            language=language,
            name=name,
            description=description,
            tools=tools,
            mcp_servers=mcp_servers,
        )
        return session

    def resume_session(self, session_id: str) -> InteractiveSession:
        """Resume existing session.

        Args:
            session_id: The session ID to resume.

        Returns:
            The session object.
        """

        isession = InteractiveSession(
            user=self.user,
            base_url=self.base_url,
            base_websockets_url=self.base_websockets_url,
            api_key=self.api_key,
            logs_processor_api_url=self.logs_processor_api_url,
        )

        isession.resume(session_id=session_id)
        return isession

    def list_sessions(self) -> list[InteractiveSession]:
        """List all active sessions for a user.

        Returns:
            list[Session]: List of sessions for the user.
        """
        ui = self.get_user_info()
        isessions = []
        for session in ui.sessions:
            isession = InteractiveSession(
                user=self.user,
                base_url=self.base_url,
                base_websockets_url=self.base_websockets_url,
                api_key=self.api_key,
                logs_processor_api_url=self.logs_processor_api_url,
            )
            isession._session = session
            isessions.append(isession)
        return isessions

    def print_sessions(self) -> None:
        """Print active sessions."""
        ui = self.get_user_info()
        if not ui:
            return
        self._display_sessions(ui.sessions)

    @staticmethod
    def _ts_to_string(ts, fmt="%Y-%m-%d %H:%M:%S"):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(fmt)

    def list_models(self) -> None:
        """List available models."""
        self._display_models(self.available_models)

    def _display_models(self, models: list[ModelInfo]) -> None:
        for model in models:
            model_table = Table(title=f"{model.model_string}", box=box.ROUNDED)
            model_table.add_column("Toolset")
            model_table.add_column("Vendor")
            model_table.add_column("Version")
            model_table.add_column("Enabled?")
            model_table.add_column("Experimental?")
            model_table.add_column("Description", overflow="fold")
            for sa in model.toolsets:
                model_table.add_row(
                    sa.name,
                    sa.vendor.name,
                    str(sa.version),
                    str(sa.is_enabled),
                    str(sa.is_experimental),
                    sa.description,
                )
            self.console.print(f"\n[{model.model_string}]")
            self.console.print(model_table)

    def _display_sessions(self, sessions: list[PublicSession]) -> None:
        if len(sessions) > 0:
            sessions_table = Table(title="Sessions", box=box.ROUNDED)
            sessions_table.add_column(
                "ID / Name", style="dim", overflow="fold", width=32
            )
            # sessions_table.add_column("Name", width=32)
            sessions_table.add_column("Description", overflow="fold")
            sessions_table.add_column("State", width=15)
            sessions_table.add_column("#Msg", width=5)
            sessions_table.add_column("#Files", width=6)
            sessions_table.add_column("Created", width=20)
            sessions_table.add_column("Updated", width=20)
            sessions_table.add_column("TTL (sec)", width=8)

            for session in sessions:
                name_and_id = f"[bold blue]{session.id}[/bold blue]\n{session.name}"
                sessions_table.add_row(
                    name_and_id,
                    session.description,
                    session.state.value,
                    str(session.num_messages),
                    str(len(session.files)),
                    SecGemini._ts_to_string(session.create_time),
                    SecGemini._ts_to_string(session.update_time),
                    str(session.ttl),
                )

            self.console.print(sessions_table)
        else:
            self.console.print("No active sessions found.", style="italic")
