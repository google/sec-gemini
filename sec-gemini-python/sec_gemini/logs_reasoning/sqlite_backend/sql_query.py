"""Translates a search tool query into an SQL query."""

import sec_gemini.logs_reasoning.logstore as ls

TEXT_FIELDS = ["timestamp_desc", "message", "enrichment"]
TIMESTAMP_FIELD = "timestamp"


def _escape_value(string: str) -> str:
  """Escapes special characters in a string value."""
  to_escape = ["\\", '"', "?", "*", "'", "%", "_"]
  output = []
  for c in string:
    if c in to_escape:
      output.append("\\")
    output.append(c)
  return "".join(output)


def _substr(field_name: str, substr: str) -> str:
  escaped = _escape_value(substr)
  return f"({field_name} LIKE '%{escaped}%' ESCAPE '\\')"


def _exist_value(field: str, values: list[str]) -> str:
  """For a given field, there exists a value that matches."""
  return " OR ".join([_substr(field, value) for value in values])


def _exist_key(fields: list[str], value: str) -> str:
  """For a given value, there exists a key that matches."""
  return " OR ".join([_substr(field, value) for field in fields])


def _not_exist_value(field: str, values: list[str]) -> str:
  """For a given field, there is no value that matches."""
  return "NOT (" + _exist_value(field, values) + ")"


def translate(
  log_type: str | None,
  order_by: ls.Order,
  limit: int,
  at_or_after: int | None,
  at_or_before: int | None,
  contains_at_least_one_of: list[str] | None,
  must_contain_all_of: list[str] | None,
  must_not_contain_any_of: list[str] | None,
) -> str:
  """Translates constraints to a CLP query fragment."""
  # Note: This function assumes trusted inputs. Consider rewriting this
  # using a parametrized SQL query instead for proper arguments escaping.
  parts = [
    "SELECT record_id, log_type, timestamp_micros, timestamp_desc, message,"
    " enrichment FROM records WHERE"
  ]
  clauses = []
  if log_type is not None:
    clauses.append(f"log_type='{log_type}'")
  if at_or_after is not None:
    clauses.append(f"timestamp_micros >= {at_or_after}")
  if at_or_before is not None:
    clauses.append(f"timestamp_micros <= {at_or_before}")
  if contains_at_least_one_of:
    # There is at least one matching combination of field-value.
    clauses.append(
      " OR ".join(
        _exist_value(key, contains_at_least_one_of) for key in TEXT_FIELDS
      )
    )
  if must_contain_all_of:
    # All values have at least one matching field.
    per_value_match = [
      "(" + _exist_key(TEXT_FIELDS, value) + ")"
      for value in must_contain_all_of
    ]
    clauses.append(" AND ".join(per_value_match))
  if must_not_contain_any_of:
    # No matching field-value pairs.
    per_key_not = [
      "(" + _not_exist_value(key, must_not_contain_any_of) + ")"
      for key in TEXT_FIELDS
    ]
    clauses.append(" AND ".join(per_key_not))
  parts.append(" AND ".join(["(" + clause + ")" for clause in clauses]))
  if order_by == ls.Order.CHRONOLOGICAL:
    parts.append("ORDER BY timestamp_micros")
  elif order_by == ls.Order.RANDOM_SAMPLE:
    parts.append("ORDER BY RANDOM()")
  parts.append(f"LIMIT {limit}")
  return " ".join(parts)
