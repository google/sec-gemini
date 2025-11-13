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

"""Translates a search tool query into a sqlite-SQL query."""

import sec_gemini.logs_reasoning.logstore as ls

TEXT_FIELDS = ["timestamp_desc", "message", "enrichment"]
TIMESTAMP_FIELD = "timestamp"


def _like_comparison_value(string: str) -> str:
  """Formats a string for substring search query."""
  to_escape = ["\\", '"', "?", "*", "'", "%", "_"]
  output = []
  for c in string:
    if c in to_escape:
      output.append("\\")
    output.append(c)
  return f"%{''.join(output)}%"


def _substr(field_name: str) -> str:
  return f"({field_name} LIKE ? ESCAPE '\\')"


def translate(
  log_type: str | None,
  order_by: ls.Order,
  limit: int,
  at_or_after: int | None,
  at_or_before: int | None,
  contains_at_least_one_of: list[str] | None,
  must_contain_all_of: list[str] | None,
  must_not_contain_any_of: list[str] | None,
) -> tuple[str, list[str | int]]:
  """Translates constraints to a sqlite-SQL query with parameters."""
  parts = [
    "SELECT record_id, log_type, timestamp_micros, timestamp_desc, message,"
    " enrichment FROM records "
  ]
  clauses = []
  params: list[int | str] = []
  if log_type is not None:
    clauses.append("log_type=?")
    params.append(log_type)
  if at_or_after is not None:
    clauses.append("timestamp_micros >= ?")
    params.append(at_or_after)
  if at_or_before is not None:
    clauses.append("timestamp_micros <= ?")
    params.append(at_or_before)
  if contains_at_least_one_of:
    # There is at least one matching combination of field-value.
    elements = []
    for raw_value in contains_at_least_one_of:
      value = _like_comparison_value(raw_value)
      for field in TEXT_FIELDS:
        elements.append(_substr(field))
        params.append(value)
    clauses.append(" OR ".join(elements))
  if must_contain_all_of:
    # All values have at least one matching field.
    elements = []
    for raw_value in must_contain_all_of:
      value = _like_comparison_value(raw_value)
      per_field_match = []
      for field in TEXT_FIELDS:
        per_field_match.append(_substr(field))
        params.append(value)
      elements.append("(" + " OR ".join(per_field_match) + ")")
    clauses.append(" AND ".join(elements))
  if must_not_contain_any_of:
    # No matching field-value pairs.
    elements = []
    for raw_value in must_not_contain_any_of:
      value = _like_comparison_value(raw_value)
      for field in TEXT_FIELDS:
        elements.append("NOT " + _substr(field))
        params.append(value)
    clauses.append(" AND ".join(elements))
  if clauses:
    parts.append("WHERE ")
    parts.append(" AND ".join(["(" + clause + ")" for clause in clauses]))
  if order_by == ls.Order.CHRONOLOGICAL:
    parts.append("ORDER BY timestamp_micros")
  elif order_by == ls.Order.RANDOM_SAMPLE:
    parts.append("ORDER BY RANDOM()")
  parts.append("LIMIT ?")
  params.append(limit)
  return " ".join(parts), params
