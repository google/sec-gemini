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

from .enums import UserType
from .session import Session
from pydantic import BaseModel, Field

class User(BaseModel):
    """"""
    id: str  = Field(..., title="User ID",
                     description="The unique identifier for the user.")

    type: UserType = Field(UserType.USER, title="User Type",
                           description="The type of user.")

    org_id: str = Field(..., title="Organization ID",
                        description="User organization.")

    api_key: str = Field(..., title="API Key",
                         description="The user's API key.")

    never_log: bool = Field(False, title="Never Log",
                            description="The user session should never be logged.")

    can_disable_logging: bool = Field(False, title="Can Disable Logging",
                                description="Whether the user is authorized to disable logging.")

    key_expire_time: int = Field(0, title="Key Expire Time",
                                 description="The Unix timestamp (in seconds) of when the key will expire.")

    tpm: int = Field(100000, title="TPM",
                     description="Tokens per minute quota.")

    rpm: int = Field(10, title="RPM",
                     description="Requests per minute quota.")


class UserInfo(BaseModel):
    """"""
    user: User = Field(..., title="User",
                       description="The user information.")
    sessions: list[Session] = Field([], title="Sessions",
                                    description="The list of users active sessions.")