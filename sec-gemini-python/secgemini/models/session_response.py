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

"Chat completion models and schemas."
from pydantic import BaseModel, Field

from .message import Message
from .usage import Usage
from .enums import ModelName, MessageType, MimeType


class SessionResponse(BaseModel):
    """
    Represents a generation response returned by the model, based on the provided input.
    """

    id: str = Field(
        ...,
        title="Thread ID",
        description="The Session ID (UUID4) passed in the request."
    )

    messages: list[Message] = Field(
        ...,
        title="Generated Messages",
        description="A list of generated message. Can be more than one if `n` is greater than 1."
    )

    status_code: int = Field(..., title="Status Code",
                             description="The status code of the message. 2xx is Okay, 4xx is a client error, 5xx is a server error.")

    status_message: str = Field(..., title="Status Message",
                                description="Explain status code reason.")

    usage: Usage = Field(..., title="Usage Statistics",
                         description="Usage statistics for the message.")


    def text(self) -> str:
        content = []
        for idx, msg in enumerate(self.messages):
            if msg.mime_type == MimeType.TEXT and msg.message_type == MessageType.RESULT:
                content.append(msg.content)
            if msg.message_type == MessageType.GROUP_END:
                if idx < len(self.messages) - 1:
                    content.append("\n")
        return " ".join(content)