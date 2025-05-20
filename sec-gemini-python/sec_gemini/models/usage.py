
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

class Usage(BaseModel):
    """
    Tracks token usage for a chat completion request and response.
    """
    prompt_tokens: int = Field(0, title="Prompt Tokens",
                               description="Number of tokens in the prompt")
    generated_tokens: int = Field(0, title="Generated Tokens",
                                  description="Number of tokens used during generation")
    total_tokens: int = Field(0, title="Total Tokens",
                              description="Total number of tokens used in the request (prompt + generation)")

    cached_token_count: int = Field(0, title="Cached Token Count",
                              description="Number of tokens used in the cached response")

    thoughts_token_count: int = Field(0, title="Thoughts Token Count",
                                      description="Number of tokens used in the thoughts")

    tool_use_prompt_token_count: int = Field(0, title="Tool Use Prompt Token Count",
                                             description="Number of tokens used in the tool use prompt")


    def tally(self, subusage: "Usage") -> None:
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
        return super().__repr__() + f" prompt_tokens={self.prompt_tokens}, generated_tokens={self.generated_tokens}, total_tokens={self.total_tokens})"