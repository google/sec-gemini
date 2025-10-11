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

from time import time
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import State, UserType
from .local_tool import LocalTool
from .message import Message
from .modelinfo import ModelInfo
from .usage import Usage


class PublicUserVendor(BaseModel):
    name: str = Field(..., title="Vendor Name")
    description: str = Field(..., title="Vendor Description")
    url: str = Field(..., title="Vendor URL")
    svg: str = Field(..., title="Vendor SVG Icon")


class PublicUser(BaseModel):
    """Only add the fields necessary to show to users."""

    id: str = Field(
        ..., title="User ID", description="The user ID this session belongs to."
    )

    org_id: str = Field(
        ...,
        title="Organization ID",
        description="The organization ID this session belongs to.",
    )

    type: UserType = Field(
        UserType.USER, title="User Type", description="The type of user."
    )

    never_log: bool = Field(
        False, title="Never Log", description="The user session should never be logged."
    )

    can_disable_logging: bool = Field(
        False,
        title="Can Disable Logging",
        description="Is user authorized to disable logging.",
    )

    key_expire_time: int = Field(
        0,
        title="Key Expire Time",
        description="The Unix timestamp (in seconds) of when the key will expire.",
    )

    tpm: int = Field(0, title="TPM", description="Tokens per minute quota.")
    rpm: int = Field(0, title="RPM", description="Requests per minute quota.")

    allow_experimental: bool = Field(
        False,
        title="Allow Experimental",
        description="Whether the user is allowed to use experimental features.",
    )
    vendors: list[PublicUserVendor] = Field(
        [], title="Vendors", description="The list of vendors the user has access to."
    )


class PublicSessionFile(BaseModel):
    """Only add the fields necessary to show to users."""

    name: str = Field(..., title="Filename", description="Name of the file.")
    size: int = Field(..., title="File size", description="Size of the file in bytes.")
    sha256: str = Field(
        ..., title="SHA256 of the file", description="SHA256 of the file."
    )
    mime_type: str = Field(..., title="Mime type", description="Mime type.")
    content_type_label: Optional[str] = Field(
        None, title="Content type label", description="Content type label."
    )


class PublicSession(BaseModel):
    """Only add the fields necessary to show to users."""

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        title="Session ID",
        description="Session unique ramdom identifier.",
    )

    user_id: str = Field(
        ..., title="User ID", description="The user ID this session belongs to."
    )

    org_id: str = Field(
        ...,
        title="Organization ID",
        description="The organization ID this session belongs to.",
    )

    model: ModelInfo = Field(
        ..., title="Model", description="Model configuration used in the session."
    )

    ttl: int = Field(
        ...,
        title="Time to Live",
        description="The time to live of the session in seconds.",
    )

    language: str = Field(
        "en", title="Language", description="The iso-code of the session language."
    )

    turns: int = Field(
        default=0,
        title="Number of Turns",
        description="The number of turns in the session.",
    )

    name: str = Field(
        ..., title="Session Name", description="Human readable session name."
    )

    description: str = Field(
        ...,
        title="Session Description",
        description="A brief description to help users remember what the session is about.",
    )

    create_time: float = Field(
        default_factory=lambda: time(),
        title="Create Time",
        description="The Unix timestamp of when the session was created.",
    )

    update_time: float = Field(
        default_factory=lambda: time(),
        title="Update Time",
        description="The Unix timestamp of when the session was last updated.",
    )

    # this is useful when we do list sessions which don't returns the messages
    num_messages: int = Field(
        default=0,
        title="Number of Messages",
        description="The number of messages in the session.",
    )

    messages: list[Message] = Field(
        default_factory=list,
        title="Messages",
        description="The list of messages comprising the session so far.",
    )

    usage: Usage = Field(
        default_factory=Usage, title="Usage", description="Session usage statistics."
    )

    can_log: bool = Field(
        ..., title="Can Log", description="Whether the session can be logged or not."
    )

    state: State = Field(
        State.START, title="State", description="The state the session belongs to."
    )

    files: list[PublicSessionFile] = Field(
        default_factory=list,
        title="Files",
        description="The list of files uploaded to the session.",
    )

    logs_table: PublicLogsTable | None = Field(
        None,
        title="Logs Table",
        description="Logs table attached to the session, if any.",
    )

    local_tools: list[LocalTool] = Field(
        default_factory=list,
        title="Local Tools",
        description="The list of local tools available for this session.",
    )


class PublicLogsTable(BaseModel):
    # Note: using an hash to identify the table is a security feature that
    # guarantees that only people having access to the logs themselves have
    # access to the table.
    blake2s: str = Field(
        ...,
        title="Blake2s hash",
        description="The blake2s hash of the log file before upload. The hash key is 'secgemini'.",
    )


class UserInfo(BaseModel):
    """"""

    user: PublicUser = Field(..., title="User", description="The user information.")
    sessions: list[PublicSession] = Field(
        [], title="Sessions", description="The list of users active sessions."
    )

    available_models: list[ModelInfo] = Field(
        [],
        title="Available Models",
        description="The list of models available to the user.",
    )
