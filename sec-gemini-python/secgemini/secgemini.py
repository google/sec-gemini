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

import os
import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from dotenv import load_dotenv
from .http import NetworkClient
from .session import InteractiveSession
from .enums import _EndPoints, _URLS
from .constants import DEFAULT_TTL
from .models import ModelName, User, UserInfo, Session
from datetime import datetime, timezone
import logging
load_dotenv()
logging.basicConfig(level=logging.WARNING)

class SecGemini:

    def __init__(self,
                 api_key: str = "",
                 model_name: str = ModelName.LATEST,
                 base_url: str = _URLS.HTTPS.value,
                 base_websockets_url: str = _URLS.WEBSOCKET.value):
        """Initializes the SecGemini API client.

        Args:
            api_key: Api key used to authenticate with SecGemini. Key can also be passed
            via the environment variable SG_API_KEY.

            model_name: Model name to use.

            base_url: Server base_url. Defaults to online server.
            base_websockets_url: Websockets base_url. Defaults to online server.

        Raises:
            ValueError: _description_
        """

        if api_key == "":
            api_key = os.getenv("SG_API_KEY")
        if not api_key:
            raise ValueError(
                "API key required: explictly pass it or set env variable SG_API_KEY (e.g in .env)."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        assert self.base_url.startswith("http"), f"Invalid base_url {base_url}"
        self.http = NetworkClient(base_url, api_key)

        self.base_websockets_url = base_websockets_url.rstrip("/")
        assert self.base_websockets_url.startswith(
            "ws"), f"Invalid base_websockets_url {base_websockets_url}"

        # check if the API is working and get user info
        ui = self.get_info()
        if not ui:
            raise ValueError("API Key is invalid or the API is down.")
        self.user = ui.user

        # FIXME check if the model is valid
        self.model_name = model_name

        self.console = Console(width=200)

    def get_info(self) -> UserInfo:
        """Return users info.

        Returns:
            UserInfo: User information.
        """
        response = self.http.get(_EndPoints.USER_INFO.value)
        if not response.ok:
            logging.error(f"Request Error: {response.error_message}")
            return None
        return UserInfo(**response.data)

    def display_info(self) -> None:
        """Display users info."""
        ui = self.get_info()
        if not ui:
            return
        if ui is None:
            print("Failed to retrieve user information.")
            return

        # User Table
        if ui.user.key_expire_time > 0:
            key_expire_time = datetime.fromtimestamp(ui.user.key_expire_time)
        else:
            key_expire_time = "Never"

        user_table = Table(title="User Information", box=box.ROUNDED)
        user_table.add_column("Attribute", style="dim", width=20)
        user_table.add_column("Value")
        user_table.add_row("Type", ui.user.type.value)
        user_table.add_row("Organization ID", ui.user.org_id)
        user_table.add_row("Key Expiration Time", key_expire_time)
        user_table.add_row("Can disable session logging?",
                           str(ui.user.can_disable_logging))
        user_table.add_row("TPM Usage", f"{ui.user.tpm_usage}/{ui.user.tpm}")
        user_table.add_row("RPM Usage", f"{ui.user.rpm_usage}/{ui.user.rpm}")

        self.console.print(user_table)

        # Session Table
        self._display_sessions(ui.sessions)

    def create_session(self,
                       name: str = "",
                       description: str = "",
                       ttl: int = DEFAULT_TTL,
                       enable_logging: bool = True) -> InteractiveSession:
        """Creates a new session.

        Args:
            name: optional session name
            description: optional session description
            ttl: live of inactive session in sec.
            enable_logging: enable/disable logging (if allowed)

        Returns:
            A new session object.
        """
        session = InteractiveSession(
            model_name=self.model_name,
            user=self.user,
            base_url=self.base_url,
            base_websockets_url=self.base_websockets_url,
            api_key=self.api_key,
            enable_logging=enable_logging)

        session.register(ttl=ttl, name=name, description=description)
        return session

    def resume_session(self, session_id: str) -> InteractiveSession:
        """ Resume existing session.

        Args:
            session_id: The session ID to resume.

        Returns:
            The session object.
        """

        session = InteractiveSession(
            model_name=self.model_name,
            user=self.user,
            base_url=self.base_url,
            base_websockets_url=self.base_websockets_url,
            api_key=self.api_key)

        session.resume(session_id)
        return session

    def get_sessions(self) -> list[InteractiveSession]:
        """Get all active sessions for a user.

        Returns:
            list[Session]: List of sessions for the user.
        """
        ui = self.get_info()
        isessions = []
        for session in ui.sessions:
            isession = InteractiveSession(
                model_name=self.model_name,
                user=self.user,
                base_url=self.base_url,
                base_websockets_url=self.base_websockets_url,
                api_key=self.api_key)
            isession._session = session
            isessions.append(isession)
        return isessions

    def list_sessions(self) -> None:
        """List active sessions."""
        ui = self.get_info()
        if not ui:
            return
        self._display_sessions(ui.sessions)

    def _ts_to_string(self, ts, fmt='%Y-%m-%d %H:%M:%S'):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(fmt)
    


    def _display_sessions(self, sessions: list[Session]) -> None:
        if len(sessions) > 0:
            sessions_table = Table(title="Sessions", box=box.ROUNDED)
            sessions_table.add_column("Session ID and Name", style="dim", overflow="fold", width=32)
            #sessions_table.add_column("Name", width=32)
            sessions_table.add_column("Description", overflow="fold")
            sessions_table.add_column("State", width=15),
            sessions_table.add_column("#\nMsg", width=5),
            sessions_table.add_column("#\nFiles", width=6),
            sessions_table.add_column("Create Timestamp", width=20)
            sessions_table.add_column("Update Timestamp", width=20)
            sessions_table.add_column("TTL (sec)", width=8)

    
            for session in sessions:
                name_and_id = f"[bold blue]{session.id}[/bold blue]\n  {session.name}"
                sessions_table.add_row(
                    # session.id,
                    # session.name,
                    name_and_id,
                    session.description,
                    session.state.value,
                    str(len(session.messages)),
                    str(len(session.files)),
                    self._ts_to_string(session.create_time),
                    self._ts_to_string(session.update_time),
                    str(session.ttl),
                )

            self.console.print(sessions_table)
        else:
            self.console.print("No active sessions found.", style="italic")
