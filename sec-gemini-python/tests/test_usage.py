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


from sec_gemini.models.usage import Usage


def test_tally_accumulates_usage_without_double_counting_cached_tokens():
  aggregate = Usage()
  subusage = Usage(
    prompt_tokens=100,
    generated_tokens=50,
    total_tokens=150,
    cached_token_count=30,
    thoughts_token_count=10,
    tool_use_prompt_token_count=5,
  )

  aggregate.tally(subusage)

  assert aggregate.prompt_tokens == 100
  assert aggregate.generated_tokens == 50
  assert aggregate.total_tokens == 150
  assert aggregate.cached_token_count == 30
  assert aggregate.thoughts_token_count == 10
  assert aggregate.tool_use_prompt_token_count == 5


def test_tally_accumulates_multiple_usages():
  aggregate = Usage()
  aggregate.tally(
    Usage(
      prompt_tokens=10,
      generated_tokens=5,
      total_tokens=15,
      cached_token_count=2,
    )
  )
  aggregate.tally(
    Usage(
      prompt_tokens=20,
      generated_tokens=10,
      total_tokens=30,
      cached_token_count=4,
    )
  )

  assert aggregate.prompt_tokens == 30
  assert aggregate.generated_tokens == 15
  assert aggregate.total_tokens == 45
  assert aggregate.cached_token_count == 6
