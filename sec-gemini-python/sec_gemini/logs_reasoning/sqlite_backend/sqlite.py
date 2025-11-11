"""Local LogStore implementation backed by a SQLite database."""

import datetime
import json
import os
import sqlite3

import sec_gemini.logs_reasoning.logstore as ls
import sec_gemini.logs_reasoning.sqlite_backend.sql_query as sq


class SQLiteStore(ls.LogStore):
  """SQLite-based LogStore implementation."""

  sqlite_db_filepath: str
  n_records_to_sample: int

  def __init__(self, sqlite_db_filepath: str, n_records_to_sample: int = 0):
    """Initializes a sqlite-backed logstore."""
    if not os.path.exists(sqlite_db_filepath):
      raise ValueError(f"No sqlite db file at: {sqlite_db_filepath}")
    with sqlite3.connect(sqlite_db_filepath) as db_connection:
      cursor = db_connection.cursor()
      cursor.execute("SELECT COUNT(*) FROM records")
      if cursor.fetchone()[0] == 0:
        raise ValueError("Database has no records.")
      cursor.execute("SELECT COUNT(*) FROM log_descriptions")
      if cursor.fetchone()[0] == 0:
        raise ValueError("Database has no log descriptions.")
    self.sqlite_db_filepath = sqlite_db_filepath
    self.n_records_to_sample = n_records_to_sample

  def _row_to_log_record_result(self, row) -> ls.LogRecordResult:
    return ls.LogRecordResult(
      record_id=row[0],
      log_type=row[1],
      timestamp=datetime.datetime.fromtimestamp(row[2] / 1_000_000),
      timestamp_desc=row[3],
      message=row[4],
      enrichment=row[5],
    )

  def _sample_records(self) -> dict[str, ls.SearchResult]:
    with sqlite3.connect(self.sqlite_db_filepath) as db:
      cursor = db.cursor()
      cursor.execute(f"""SELECT log_type, json_group_array(record)
FROM (
  SELECT
    log_type,
    json_array(record_id, log_type, timestamp_micros,
                   timestamp_desc, message, enrichment) AS record,
    ROW_NUMBER() OVER (PARTITION BY log_type ORDER BY RANDOM()) AS rn
  FROM records)
WHERE rn <= {self.n_records_to_sample}
GROUP BY log_type""")
      result = {}
      for row in cursor.fetchall():
        log_type, serialized_records = row
        records = []
        for serialized_record in json.loads(serialized_records):
          records.append(
            self._row_to_log_record_result(json.loads(serialized_record))
          )
        result[log_type] = ls.SearchResult(
          status=ls.ResultStatus.SUCCESS, error_messages=None, results=records
        )
      return result

  def describe_logs(self) -> ls.LogDescriptions:
    """Implementation of the logs description functionality."""
    log_type_to_description = {}
    with sqlite3.connect(self.sqlite_db_filepath) as db:
      cursor = db.cursor()
      cursor.execute("SELECT log_type, description FROM log_descriptions")
      for row in cursor.fetchall():
        log_type_to_description[row[0]] = row[1]

      log_type_to_per_day_counts = {}
      cursor.execute(
        "SELECT log_type, DATE(timestamp_micros / 1000000, 'unixepoch'),"
        " COUNT(*) FROM records GROUP BY 1, 2"
      )
      for row in cursor.fetchall():
        log_type, date, count = row
        if log_type not in log_type_to_per_day_counts:
          log_type_to_per_day_counts[log_type] = []
        log_type_to_per_day_counts[log_type].append((date, count))

    log_type_to_samples = self._sample_records()

    result = ls.LogDescriptions(
      status=ls.ResultStatus.SUCCESS, error_messages=None, descriptions=[]
    )
    for log_type, per_day_counts in log_type_to_per_day_counts.items():
      desc = log_type_to_description.get(log_type, "description not provided")
      examples = []
      if log_type in log_type_to_samples:
        r = log_type_to_samples[log_type]
        if r.status == ls.ResultStatus.SUCCESS:
          examples = r.results
      result.descriptions.append(
        ls.LogDescription(
          log_type=log_type,
          description=desc,
          per_day_counts=per_day_counts,
          examples=examples,
        )
      )
    return result

  def search_logs(
    self,
    log_type: str | None,
    limit: int,
    at_or_after: datetime.datetime | None,
    at_or_before: datetime.datetime | None,
    contains_at_least_one_of: list[str] | None,
    must_contain_all_of: list[str] | None,
    must_not_contain_any_of: list[str] | None,
    order_by: ls.Order,
  ) -> ls.SearchResult:
    """Implementation of the logs search functionality."""
    if at_or_after is not None:
      at_or_after_us = int(at_or_after.timestamp() * 1_000_000)
    else:
      at_or_after_us = None
    if at_or_before is not None:
      at_or_before_us = int(at_or_before.timestamp() * 1_000_000)
    else:
      at_or_before_us = None

    query = sq.translate(
      log_type,
      order_by,
      limit,
      at_or_after_us,
      at_or_before_us,
      contains_at_least_one_of,
      must_contain_all_of,
      must_not_contain_any_of,
    )

    with sqlite3.connect(self.sqlite_db_filepath) as db_connection:
      cursor = db_connection.cursor()
      results = cursor.execute(query)

      records = []
      for row in results.fetchall():
        records.append(self._row_to_log_record_result(row))

      return ls.SearchResult(
        status=ls.ResultStatus.SUCCESS, error_messages=None, results=records
      )
