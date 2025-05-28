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


from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field

from .message import Message


class SessionRequest(BaseModel):
    """
    Schema for the request body for triggering a model generation.
    """

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        title="Session ID",
        description="The Session ID (UUID4) this request belongs to.",
    )

    messages: List[Message] = Field(
        ..., title="Messages", description="new query messages"
    )
