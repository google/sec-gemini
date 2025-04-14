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

from uuid import uuid4
from pydantic import BaseModel, Field
import random
from time import time
from .enums import State, MessageType, MimeType
from .message import Message
from .usage import Usage

class SessionFile(BaseModel):
    """
    Represents a file that was uploaded.
    """

    filename: str = Field(..., title="Filename",
                          description="The name of the file.")

    original_filename: str = Field(..., title="Original Filename",
                                   description="The original name of the file.")

    mime_type: MimeType = Field(..., title="Mime Type",
                                description="The mime type of the file.")


class Session(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex,
                    title="Session ID",
                    description="Session unique ramdom identifier.")

    user_id: str = Field(...,
                         title="User ID",
                         description="The user ID this session belongs to.")

    org_id: str = Field(...,
                        title="Organization ID",
                        description="The organization ID this session belongs to.")

    ttl: int = Field(...,
                     title="Time to Live",
                     description="The time to live of the session in seconds.")

    name: str = Field(...,
                      title="Session Name",
                      description="Human readable session name.")

    description: str = Field(...,
                             title="Session Description",
                             description="A brief description to help users remember what the session is about.")

    create_time: int = Field(default_factory=lambda: int(time()),
                             title="Create Time",
                           description="The Unix timestamp (in seconds) of when the session was created.")

    update_time: int = Field(default_factory=lambda: int(time()),
                             title="Update Time",
                             description="The Unix timestamp (in seconds) of when the session was last updated.")

    messages: list[Message] = Field(default_factory=list,
                                    title="Messages",
                                    description="The list of messages comprising the session so far.")

    usage: Usage = Field(default_factory=Usage,
                         title="Usage",
                         description="Session usage statistics.")

    can_log: bool = Field(default=True,
                          title="Can Log",
                          description="Whether the session can be logged or not.")

    state: State = Field(State.START,
                          title="State",
                          description="The state the session belongs to.")

    files : list[SessionFile] = Field(default_factory=list,
                                      title="Files",
                                      description="The list of files uploaded to the session.")


    @property
    def key(self) -> str:
        "cache key"
        return f"{self.org_id}:{self.user_id}:{self.id}"

    @property
    def conversation(self) -> list[Message]:
        "Return the filtered list of user facing messages"
        conversation = []
        for m in self.messages:

            # user query
            if m.message_type == MessageType.QUERY and m.mime_type == MimeType.TEXT:
                conversation.append(m)
            # response
            if m.message_type == MessageType.RESULT and m.mime_type == MimeType.TEXT:
                conversation.append(m)
        return conversation