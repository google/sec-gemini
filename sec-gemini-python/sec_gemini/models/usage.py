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

from enum import Enum

from pydantic import BaseModel, Field


class Usage(BaseModel):
  """
  Tracks token usage for a chat completion request and response.
  """

  prompt_tokens: int = Field(
    0, title="Prompt Tokens", description="Number of tokens in the prompt"
  )
  generated_tokens: int = Field(
    0,
    title="Generated Tokens",
    description="Number of tokens used during generation",
  )
  total_tokens: int = Field(
    0,
    title="Total Tokens",
    description="Total number of tokens used in the request (prompt + generation)",
  )

  cached_token_count: int = Field(
    0,
    title="Cached Token Count",
    description="Number of tokens used in the cached response",
  )

  thoughts_token_count: int = Field(
    0,
    title="Thoughts Token Count",
    description="Number of tokens used in the thoughts",
  )

  tool_use_prompt_token_count: int = Field(
    0,
    title="Tool Use Prompt Token Count",
    description="Number of tokens used in the tool use prompt",
  )

  prompt_tokens_details: list[ModalityTokenCount] | None = Field(
    None, title="Prompt Tokens Details"
  )

  def cost(self, model_name: str) -> float:
    """
    Calculate the cost of the usage based on the model name.
    """
    # price per model
    PRICE = {
      "flash": {"input": 0.15, "thinking_output": 3.5, "output": 0.6},
      "pro": {"input": 1.25, "thinking_output": 10, "output": 10},
    }

    if self.thoughts_token_count > 0:
      if "flash" in model_name:
        icost = PRICE["flash"]["input"]
        ocost = PRICE["flash"]["thinking_output"]
      else:
        icost = PRICE["pro"]["input"]
        ocost = PRICE["pro"]["thinking_output"]
    else:
      if "flash" in model_name:
        icost = PRICE["flash"]["input"]
        ocost = PRICE["flash"]["output"]
      else:
        icost = PRICE["pro"]["input"]
        ocost = PRICE["pro"]["output"]

    total = ocost * (self.generated_tokens / 1_000_000)
    total += ocost * (self.thoughts_token_count / 1_000_000)
    total += icost * (self.prompt_tokens / 1_000_000)
    total += icost * (self.cached_token_count / 1_000_000)
    return total

  def tally(self, subusage: Usage) -> None:
    """
    Update the usage with the given values.
    """
    if subusage:
      self.prompt_tokens += subusage.prompt_tokens
      self.generated_tokens += subusage.generated_tokens
      self.total_tokens += subusage.total_tokens
      self.cached_token_count += subusage.cached_token_count
      self.thoughts_token_count += subusage.thoughts_token_count
      self.tool_use_prompt_token_count += subusage.tool_use_prompt_token_count
      self.total_tokens += subusage.cached_token_count

  def __repr__(self):
    return (
      super().__repr__()
      + f" prompt_tokens={self.prompt_tokens}, generated_tokens={self.generated_tokens}, total_tokens={self.total_tokens})"
    )


# FIXME: Taken from google/genai/types.py; we do this to avoid importing genai, which
# adds one second to the bootstrap time.
class ModalityTokenCount(BaseModel):
  """Represents token counting info for a single modality."""

  modality: MediaModality | None = Field(
    default=None,
    description="""The modality associated with this token count.""",
  )
  token_count: int | None = Field(
    default=None, description="""Number of tokens."""
  )


# FIXME: Taken from google/genai/types.py; we do this to avoid importing genai, which
# adds one second to the bootstrap time.
class MediaModality(str, Enum):
  """Server content modalities."""

  MODALITY_UNSPECIFIED = "MODALITY_UNSPECIFIED"
  """The modality is unspecified."""
  TEXT = "TEXT"
  """Plain text."""
  IMAGE = "IMAGE"
  """Images."""
  VIDEO = "VIDEO"
  """Video."""
  AUDIO = "AUDIO"
  """Audio."""
  DOCUMENT = "DOCUMENT"
  """Document, e.g. PDF."""
