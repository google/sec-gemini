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

import collections
import datetime
import sqlite3

import pytest

import sec_gemini.logs_reasoning.logstore as ls
from sec_gemini.logs_reasoning.sqlite_backend.sqlite import SQLiteStore

RECORDS = [
  ls.LogRecordResult(
    record_id="id1",
    log_type="syslog",
    timestamp=datetime.datetime(2025, 11, 1, 0, 0, 0),
    timestamp_desc="START",
    message="message1",
    enrichment="enrichment1",
  ),
  ls.LogRecordResult(
    record_id="id2",
    log_type="syslog",
    timestamp=datetime.datetime(2025, 11, 2, 0, 0, 1),
    timestamp_desc="STOP",
    message="message2",
    enrichment="enrichment2 .*",
  ),
  ls.LogRecordResult(
    record_id="id3",
    log_type="network",
    timestamp=datetime.datetime(2025, 11, 1, 0, 0, 2),
    timestamp_desc="START",
    message="message3",
    enrichment="enrichment3 special_character",
  ),
  ls.LogRecordResult(
    record_id="id4",
    log_type="network",
    timestamp=datetime.datetime(2025, 11, 1, 0, 0, 3),
    timestamp_desc="STOP",
    message="message4",
    enrichment="enrichment4 special\\character",
  ),
]


@pytest.fixture(scope="module")
def sqlite_db_filepath(tmp_path_factory):
  """Create and populate a test logs DB."""
  log_descriptions = [("syslog", "system logs"), ("network", "network logs")]

  filename = tmp_path_factory.mktemp("sqlite_data") / "test.db"
  with sqlite3.connect(filename) as connection:
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE log_descriptions
                       (log_type TEXT, description TEXT)""")
    for log_type, description in log_descriptions:
      cursor.execute(
        "INSERT INTO log_descriptions (log_type, description) VALUES (?, ?)",
        (log_type, description),
      )

    cursor.execute("""CREATE TABLE records
                       (record_id TEXT,
                       log_type TEXT,
                       timestamp_micros INTEGER,
                       timestamp_desc TEXT,
                       message TEXT,
                       enrichment TEXT)""")
    for r in RECORDS:
      cursor.execute(
        "INSERT INTO records (record_id, log_type, timestamp_micros,"
        "timestamp_desc, message, enrichment) VALUES (?, ?, ?, ?, ?, ?)",
        (
          r.record_id,
          r.log_type,
          int(r.timestamp.timestamp() * 1_000_000),
          r.timestamp_desc,
          r.message,
          r.enrichment,
        ),
      )

  return filename


def test_describe_logs(sqlite_db_filepath):
  store = SQLiteStore(sqlite_db_filepath, n_records_to_sample=1)
  descriptions = store.describe_logs()
  assert descriptions.status == ls.ResultStatus.SUCCESS
  assert descriptions.error_messages is None
  assert len(descriptions.descriptions) == 2
  log_type_to_description = {}
  for description in descriptions.descriptions:
    log_type_to_description[description.log_type] = description
  assert log_type_to_description["syslog"].description == "system logs"
  assert log_type_to_description["network"].description == "network logs"
  assert log_type_to_description["syslog"].per_day_counts == [
    ("2025-11-01", 1),
    ("2025-11-02", 1),
  ]
  assert log_type_to_description["network"].per_day_counts == [
    ("2025-11-01", 2)
  ]
  assert len(log_type_to_description["syslog"].examples) == 1
  syslog_example = log_type_to_description["syslog"].examples[0]
  assert syslog_example == RECORDS[0] or syslog_example == RECORDS[1]
  assert len(log_type_to_description["network"].examples) == 1
  network_example = log_type_to_description["network"].examples[0]
  assert network_example == RECORDS[2] or network_example == RECORDS[3]


def query(
  log_type=None,
  limit=10,
  at_or_after=None,
  at_or_before=None,
  contains_at_least_one_of=None,
  must_contain_all_of=None,
  must_not_contain_any_of=None,
  order=ls.Order.CHRONOLOGICAL,
):
  q = collections.namedtuple(
    "query",
    [
      "log_type",
      "limit",
      "at_or_after",
      "at_or_before",
      "contains_at_least_one_of",
      "must_contain_all_of",
      "must_not_contain_any_of",
      "order",
    ],
  )
  return q(
    log_type,
    limit,
    at_or_after,
    at_or_before,
    contains_at_least_one_of,
    must_contain_all_of,
    must_not_contain_any_of,
    order,
  )


@pytest.mark.parametrize(
  "query,expected_records",
  [
    # returns all, sort by time
    (query(), (0, 2, 3, 1)),
    # case insensitive
    (query(contains_at_least_one_of=["start"]), (0, 2)),
    # time interval
    (
      query(
        at_or_after=datetime.datetime(2025, 11, 1, 0, 0, 2),
        at_or_before=datetime.datetime(2025, 11, 1, 0, 0, 3),
      ),
      (2, 3),
    ),
    # log type
    (query(log_type="syslog"), (0, 1)),
    # any of
    (query(contains_at_least_one_of=["message1", "enrichment3"]), (0, 2)),
    # all of
    (query(must_contain_all_of=["start", "message3"]), (2,)),
    # none of
    (query(must_not_contain_any_of=["stop", "enrichment1"]), (2,)),
    # limit
    (query(limit=1), (0,)),
    # special character _
    (query(contains_at_least_one_of=["_"]), (2,)),
    # special character \
    (query(contains_at_least_one_of=["\\"]), (3,)),
    # special characters .*
    (query(contains_at_least_one_of=[".*"]), (1,)),
    # complex query
    (
      query(
        contains_at_least_one_of=["start", "message2"],
        must_contain_all_of=["start", "message", "enrichment"],
        must_not_contain_any_of=["enrichment1"],
      ),
      (2,),
    ),
  ],
)
def test_search(sqlite_db_filepath, query, expected_records):
  store = SQLiteStore(sqlite_db_filepath)
  results = store.search_logs(
    log_type=query.log_type,
    limit=query.limit,
    at_or_after=query.at_or_after,
    at_or_before=query.at_or_before,
    contains_at_least_one_of=query.contains_at_least_one_of,
    must_contain_all_of=query.must_contain_all_of,
    must_not_contain_any_of=query.must_not_contain_any_of,
    order_by=query.order,
  )

  assert results.status == ls.ResultStatus.SUCCESS
  assert results.error_messages is None
  assert len(results.results) == len(expected_records)
  assert results.results == [RECORDS[i] for i in expected_records]


def test_random(sqlite_db_filepath):
  store = SQLiteStore(sqlite_db_filepath)
  results = store.search_logs(
    log_type=None,
    limit=10,
    at_or_after=None,
    at_or_before=None,
    contains_at_least_one_of=None,
    must_contain_all_of=None,
    must_not_contain_any_of=None,
    order_by=ls.Order.RANDOM_SAMPLE,
  )

  assert results.status == ls.ResultStatus.SUCCESS
  assert results.error_messages is None
  assert len(results.results) == 4
  for record in RECORDS:
    assert record in results.results


def test_sec_gemini_tools(sqlite_db_filepath):
  store = SQLiteStore(sqlite_db_filepath)
  tools = store.make_tools()
  assert len(tools) == 2
  if tools[0].__name__ == "sec_gemini_describe_logs":
    describe_fn = tools[0]
    search_fn = tools[1]
  else:
    describe_fn = tools[1]
    search_fn = tools[0]

  describe_fn_result_json = describe_fn()
  describe_fn_result = ls.LogDescriptions.model_validate_json(
    describe_fn_result_json
  )
  assert describe_fn_result.status == ls.ResultStatus.SUCCESS
  assert describe_fn_result.error_messages is None
  assert len(describe_fn_result.descriptions) == 2

  search_fn_result_json = search_fn(
    log_type=None,
    limit=10,
    at_or_after=None,
    at_or_before=None,
    contains_at_least_one_of=None,
    must_contain_all_of=None,
    must_not_contain_any_of=None,
    order_by="CHRONOLOGICAL",
  )
  search_fn_result = ls.SearchResult.model_validate_json(search_fn_result_json)
  assert search_fn_result.status == ls.ResultStatus.SUCCESS
  assert search_fn_result.error_messages is None
  assert len(search_fn_result.results) == 4
  assert search_fn_result.results == [
    RECORDS[0],
    RECORDS[2],
    RECORDS[3],
    RECORDS[1],
  ]
