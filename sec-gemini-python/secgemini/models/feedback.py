
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


from pydantic import BaseModel, Field
from .enums import FeedbackType


class Feedback(BaseModel):
    """Represents a feedback to the session."""

    session_id: str = Field(..., title="Session ID",
                            description="The session ID this feedback should be attached to.")

    group_id: str = Field('', title="Group ID",
                          description="The message group ID this feedback should be attached to.")

    type: FeedbackType = Field(..., title="Feedback Type",
                                         description="The type of feedback.")

    score: int = Field(..., title="Score",
                       description="The score of the feedback.")

    comment: str = Field(..., title="Comment",
                         description="The comment of the feedback.")
