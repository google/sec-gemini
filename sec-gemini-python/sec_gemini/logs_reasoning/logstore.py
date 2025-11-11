"""LogStore interface definitions."""

import datetime
import enum
from collections.abc import Callable

import pydantic


class ResultStatus(enum.Enum):
  """The status of the local search/describe call response."""
  SUCCESS = 1
  ERROR = 2


class LogRecordResult(pydantic.BaseModel):
  """A single log record result."""

  # Unique identifier of a log record. Prefer shorter strings.
  record_id: str
  # The name of the log type the log record belongs to, e.g. 'syslog',
  # 'windows:evtx', ...
  log_type: str
  # Timestamp of the log record.
  timestamp: datetime.datetime
  # Description of the timestamp semantics, e.g. 'creation time',
  # 'modification time', etc.
  timestamp_desc: str
  # The raw content of the log record.
  message: str
  # Any additional contextual enrichment for entities present in the log
  # message, for example from detection systems.
  enrichment: str | None


class SearchResult(pydantic.BaseModel):
  """Represents the results of the local search call."""
  status: ResultStatus
  results: list[LogRecordResult]
  error_messages: list[str] | None = None


class LogDescription(pydantic.BaseModel):
  """Describes the contents of a single log source."""

  # The name of the log type, e.g. 'syslog', 'windows:evtx', ...
  log_type: str
  # A short description of the type of log records in the log_type. Add any
  # specific interpretation instructions here.
  description: str | None
  # Each tuple is a date-count, e.g., ('2025-11-27', 124567)
  per_day_counts: list[tuple[str, int]]
  # A set of log records, usually sampled at random, from the log source.
  examples: list[LogRecordResult]


class LogDescriptions(pydantic.BaseModel):
  """Represents the results of the local describe call."""
  status: ResultStatus
  descriptions: list[LogDescription]
  error_messages: list[str] | None = None


class Order(enum.Enum):
  """Specifies the order in which to return the search results."""
  CHRONOLOGICAL = 1
  RANDOM_SAMPLE = 2


class LogStore:
  """Abstract base class for a log store.

  Client-side application must subclass this interface and
  provide implementations for describe_logs() and search_logs().
  An example is provided in sqlite.py.
  """

  def describe_logs(self) -> LogDescriptions:
    """User-provided descriptions of the available logs."""
    raise NotImplementedError()

  def search_logs(
    self,
    log_type: str | None,
    limit: int,
    at_or_after: datetime.datetime | None,
    at_or_before: datetime.datetime | None,
    contains_at_least_one_of: list[str] | None,
    must_contain_all_of: list[str] | None,
    must_not_contain_any_of: list[str] | None,
    order_by: Order,
  ) -> SearchResult:
    """User-provided search function over the logs.

    Keyword search must be case-insensitive.

    Args:
      log_type: The log type to search, as returned by describe_logs(). If None,
        search all log types.
      limit: The maximum number of results to return.
      at_or_after: The minimum timestamp of the results.
      at_or_before: The maximum timestamp of the results.
      contains_at_least_one_of: The retrieved records contain at least one of
        these strings as a substring of the message, enrichment or
        timestamp_desc fields.
      must_contain_all_of: The retrieved records each contain all of these
        strings as substrings of either the message, enrichment or
        timestamp_desc fields.
      must_not_contain_any_of: Excludes records which contain any of these
        strings as a substring of the message, enrichement or timestamp_desc
        fields.
      order_by: The ordering of the results.
    """
    raise NotImplementedError()

  def make_tools(self) -> list[Callable]:  # pylint: disable=g-bare-generic
    """Returns the tools required for Sec-Gemini's log reasoning capability."""
    result = []

    def sec_gemini_describe_logs() -> str:
      """Internal Sec-Gemini tool."""
      try:
        descriptions = self.describe_logs()
      except Exception as e:  # pylint: disable=broad-except
        descriptions = LogDescriptions(
          status=ResultStatus.ERROR,
          error_messages=[
            (
              "Local logs description call raised an exception (SG client"
              " side error):"
            ),
            str(e),
          ],
          descriptions=[],
        )
      return descriptions.model_dump_json()

    result.append(sec_gemini_describe_logs)

    def sec_gemini_search_log(
      log_type: str | None,
      limit: int,
      at_or_after: str | None,
      at_or_before: str | None,
      contains_at_least_one_of: list[str] | None,
      must_contain_all_of: list[str] | None,
      must_not_contain_any_of: list[str] | None,
      order_by: str,
    ) -> str:
      """Internal Sec-Gemini tool."""
      try:
        results = self.search_logs(
          log_type=log_type,
          limit=limit,
          at_or_after=datetime.datetime.fromisoformat(at_or_after)
          if at_or_after
          else None,
          at_or_before=datetime.datetime.fromisoformat(at_or_before)
          if at_or_before
          else None,
          contains_at_least_one_of=contains_at_least_one_of,
          must_contain_all_of=must_contain_all_of,
          must_not_contain_any_of=must_not_contain_any_of,
          order_by=Order[order_by.upper()],
        )
      except Exception as e:  # pylint: disable=broad-except
        results = SearchResult(
          status=ResultStatus.ERROR,
          error_messages=[
            (
              "Local log search call raised an exception (SG client side"
              " error):"
            ),
            str(e),
          ],
          results=[],
        )
      return results.model_dump_json()

    result.append(sec_gemini_search_log)

    return result
