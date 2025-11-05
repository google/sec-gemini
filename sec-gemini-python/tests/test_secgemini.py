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

import asyncio
import copy
import hashlib
import ipaddress
import json
import os
import traceback

import pytest
import websockets
from conftest import MOCK_SEC_GEMINI_API_HOST
from pytest_httpx import HTTPXMock
from utils import (
  async_require_env_variable,
  parse_secgemini_response,
  require_env_variable,
)

from sec_gemini import SecGemini
from sec_gemini.models.enums import (
  MessageType,
  MimeType,
  ResponseStatus,
  Role,
  State,
)
from sec_gemini.models.message import ROOT_ID, Message
from sec_gemini.models.public import PublicSession, PublicSessionFile, UserInfo
from sec_gemini.session import InteractiveSession


def test_user_info_is_received_correctly(
  mock_secgemini_client: SecGemini, mock_user: UserInfo, httpx_mock: HTTPXMock
):
  httpx_mock.add_response(
    url=mock_secgemini_client.base_url + "/v1/user/info",
    json=mock_user.model_dump(),
  )
  info = mock_secgemini_client.get_user_info()
  assert info.user.id == mock_user.user.id
  assert info.user.org_id == mock_user.user.org_id
  assert info.user.type == mock_user.user.type
  assert info.user.key_expire_time == mock_user.user.key_expire_time
  assert info.user.tpm == mock_user.user.tpm
  assert info.user.rpm == mock_user.user.rpm
  assert info.user.allow_experimental == mock_user.user.allow_experimental
  assert info.user.vendors == mock_user.user.vendors
  assert info.user.never_log == mock_user.user.never_log
  assert info.user.can_disable_logging == mock_user.user.can_disable_logging


# TODO: test that the available models are parsed correctly


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_resume_session(
  mock_secgemini_client: SecGemini,
  httpx_mock: HTTPXMock,
  mock_public_session: PublicSession,
):
  httpx_mock.add_response(
    url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000/v1/session/get?session_id={mock_public_session.id}",
    method="GET",
    json=mock_public_session.model_dump(),
  )
  session = mock_secgemini_client.resume_session(
    session_id=mock_public_session.id
  )
  assert session is not None
  assert isinstance(session, InteractiveSession)
  assert session.id == mock_public_session.id


@pytest.mark.httpx_mock
def test_create_session_invalid_model_name(mock_secgemini_client: SecGemini):
  with pytest.raises(
    ValueError,
    match="Invalid model string as input: ",
  ):
    mock_secgemini_client.create_session(model="invalid_model")


@pytest.mark.httpx_mock
def test_create_session_invalid_model_type(mock_secgemini_client: SecGemini):
  with pytest.raises(
    ValueError,
    match="Invalid model as input: ",
  ):
    mock_secgemini_client.create_session(model=123)  # type: ignore


def test_init_no_api_key():
  with pytest.raises(ValueError, match="API key required"):
    SecGemini(
      api_key="",
      base_url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000",
      base_websockets_url=f"ws://{MOCK_SEC_GEMINI_API_HOST}:8000",
    )


def test_init_invalid_base_url():
  with pytest.raises(ValueError, match="Invalid base_url"):
    SecGemini(
      api_key="test_key",
      base_url="invalid_url",
      base_websockets_url=f"ws://{MOCK_SEC_GEMINI_API_HOST}:8000",
    )


def test_init_invalid_websockets_url():
  with pytest.raises(ValueError, match="Invalid base_websockets_url"):
    SecGemini(
      api_key="test_key",
      base_url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000",
      base_websockets_url="invalid_ws_url",
    )


@pytest.mark.httpx_mock
def test_init_get_user_info_fails(httpx_mock: HTTPXMock):
  httpx_mock.add_response(
    url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000/v1/user/info",
    method="GET",
    status_code=500,
  )
  with pytest.raises(Exception, match="Request Error: "):
    SecGemini(
      api_key="test_key",
      base_url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000",
      base_websockets_url=f"ws://{MOCK_SEC_GEMINI_API_HOST}:8000",
    )


@pytest.mark.httpx_mock
def test_get_info_request_error(
  mock_secgemini_client: SecGemini, httpx_mock: HTTPXMock
):
  # secgemini_client_with_models fixture mocks a successful get_info for __init__.
  # We need a new mock for a subsequent call to get_info that fails.
  httpx_mock.add_response(
    url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000/v1/user/info",
    method="GET",
    status_code=401,  # Simulate an authorization error for example
    json={
      "detail": "Authentication credentials were not provided or were invalid."
    },
  )
  with pytest.raises(Exception, match="Request Error: "):
    _ = mock_secgemini_client.get_user_info()


@require_env_variable("SEC_GEMINI_API_KEY")
def test_simple_query(secgemini_client: SecGemini):
  session = secgemini_client.create_session()
  resp = session.query(
    "This is a test query as part of an automated integration test. "
    "As a reply, please just output the word 'fulmicotone', nothing else."
  )
  content = resp.text().strip()
  assert content.find("fulmicotone") >= 0


@require_env_variable("SEC_GEMINI_API_KEY")
def test_query_get_ips(secgemini_client: SecGemini):
  session = secgemini_client.create_session()

  resp = session.query(
    'What are the IP addresses of google.com? Reply with this format: {"ips": ["1.2.3.4", ...]}. '
    "Do NOT add anything else, not even ``` or similar things. "
    "In other words, the raw output must be a valid JSON."
  )

  content = resp.text().strip()
  print(f"Raw response: {content}")

  content = parse_secgemini_response(content)
  print(f"Parsed response: {content}")

  def is_valid_ip(ip_str: str) -> bool:
    # This supports both ipv4 and ipv6
    try:
      ipaddress.ip_address(ip_str)
      return True
    except ValueError:
      return False

  info = json.loads(content)
  assert "ips" in info.keys()
  assert len(info["ips"]) > 0
  for ip in info["ips"]:
    assert is_valid_ip(ip)
  print("Answer passed all checks.")


@require_env_variable("SEC_GEMINI_API_KEY")
def test_query_with_virustotal_tool_benign(secgemini_client: SecGemini):
  session = secgemini_client.create_session()
  resp = session.query(
    "Is file 82aac168acbadca3b05a6c6aa2200aa87ae464ad415230f266e745f69fa130d8 benign or malicious? "
    "Just output one word, 'benign' or 'malicious'. If uncertain, take your best guess."
  )
  content = resp.text().strip()
  content = parse_secgemini_response(content)
  assert content == "benign"


@require_env_variable("SEC_GEMINI_API_KEY")
def test_query_with_virustotal_tool_malicious(secgemini_client: SecGemini):
  session = secgemini_client.create_session()
  resp = session.query(
    "Is file a188ff24aec863479408cee54b337a2fce25b9372ba5573595f7a54b784c65f8 benign or malicious? "
    "Just output one word, 'benign' or 'malicious'. If uncertain, take your best guess."
  )
  content = resp.text().strip()
  content = parse_secgemini_response(content)
  assert content == "malicious"


@require_env_variable("SEC_GEMINI_API_KEY")
def test_query_with_attachment(
  secgemini_client: SecGemini, test_pdf_info: tuple[str, bytes]
):
  pdf_filename, pdf_content = test_pdf_info

  session = secgemini_client.create_session()
  res = session.attach_file(pdf_filename, pdf_content)
  assert res is not None
  assert len(session.files) == 1

  resp = session.query(
    "The file in attachment should be about a tool in machine learning. What is the name of the tool?"
    "Just output one word, nothing else."
  )
  content = resp.text().strip()
  content = parse_secgemini_response(content)
  assert content.lower() == "retsim"


@require_env_variable("SEC_GEMINI_API_KEY")
def test_session_attachments_apis(
  secgemini_client: SecGemini,
  test_pdf_info: tuple[str, bytes],
  test_png_info: tuple[str, bytes],
  test_jpeg_info: tuple[str, bytes],
):
  def check_session_files(
    session_files: list[PublicSessionFile],
    test_files_infos: list[tuple[str, bytes, str, str]],
  ) -> None:
    assert len(session_files) == len(test_files_infos)
    for session_file, test_file_info in zip(
      session_files, test_files_infos, strict=False
    ):
      assert session_file.name == test_file_info[0]

  pdf_filename, pdf_content = test_pdf_info
  png_filename, png_content = test_png_info
  jpeg_filename, jpeg_content = test_jpeg_info

  test_files_infos = [
    (pdf_filename, pdf_content, "application/pdf", "pdf"),
    (png_filename, png_content, "image/png", "png"),
    (jpeg_filename, jpeg_content, "image/jpeg", "jpeg"),
  ]

  session = secgemini_client.create_session()

  for test_file_idx, (
    test_filename,
    test_content,
    test_mime_type,
    test_content_type_label,
  ) in enumerate(test_files_infos):
    attach_res = session.attach_file(test_filename, test_content)
    assert attach_res is not None
    assert attach_res.name == test_filename
    assert attach_res.size == len(test_content)
    assert attach_res.sha256 == hashlib.sha256(test_content).hexdigest()
    assert attach_res.mime_type == test_mime_type
    assert attach_res.content_type_label == test_content_type_label
    assert len(session.files) == test_file_idx + 1
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(3)
  assert detach_res is False
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(-1)
  assert detach_res is False
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(1)
  test_files_infos.pop(1)
  assert detach_res is True
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(2)
  assert detach_res is False
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(0)
  test_files_infos.pop(0)
  assert detach_res is True
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(1)
  assert detach_res is False
  check_session_files(session.files, test_files_infos)

  detach_res = session.detach_file(0)
  test_files_infos.pop(0)
  assert detach_res is True
  check_session_files(session.files, test_files_infos)
  assert len(session.files) == 0

  detach_res = session.detach_file(0)
  assert detach_res is False


@require_env_variable("SEC_GEMINI_API_KEY")
def test_session_list_and_delete(secgemini_client: SecGemini):
  isessions = secgemini_client.list_sessions()
  for isession in isessions:
    isession.delete()
  assert len(secgemini_client.list_sessions()) == 0

  s1 = secgemini_client.create_session()
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 1
  assert isessions[0].id == s1.id

  s2 = secgemini_client.create_session()
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 2
  assert isessions[1].id == s2.id

  s3 = secgemini_client.create_session()
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 3
  assert isessions[2].id == s3.id

  assert isessions[1].id == s2.id
  res = isessions[1].delete()
  assert res is True
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 2
  assert isessions[0].id == s1.id
  assert isessions[1].id == s3.id

  s4 = secgemini_client.create_session()
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 3
  assert isessions[2].id == s4.id

  res = isessions[0].delete()
  assert res is True
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 2
  assert isessions[0].id == s3.id
  assert isessions[1].id == s4.id

  fake_isession = copy.copy(isessions[0])
  assert fake_isession._session is not None
  fake_isession._session.id = "0" * len(fake_isession._session.id)
  res = fake_isession.delete()
  assert res is False

  res = isessions[1].delete()
  assert res is True
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 1
  assert isessions[0].id == s3.id

  res = isessions[0].delete()
  assert res is True
  isessions = secgemini_client.list_sessions()
  assert len(isessions) == 0


@require_env_variable("SEC_GEMINI_API_KEY")
def test_report_feedback_and_bug_report(secgemini_client: SecGemini):
  session = secgemini_client.create_session()
  res = session.send_bug_report("this is a bug", "group X")
  assert res is True

  res = session.send_feedback(3, "this is a comment", "group Y")
  assert res is True


@pytest.mark.asyncio
@async_require_env_variable("SEC_GEMINI_API_KEY")
async def test_simple_query_ws(secgemini_client: SecGemini):
  query = (
    "This is a test query as part of an automated integration test. "
    "As a reply, please just output the word 'fulmicotone', nothing else."
  )
  content = await query_via_websocket(secgemini_client, query)
  content = parse_secgemini_response(content)
  assert content.find("fulmicotone") >= 0


@pytest.mark.asyncio
@async_require_env_variable("SEC_GEMINI_API_KEY")
async def test_query_with_virustotal_tool_malicious_ws(
  secgemini_client: SecGemini,
):
  query = (
    "Is file a188ff24aec863479408cee54b337a2fce25b9372ba5573595f7a54b784c65f8 benign or malicious? "
    "Just output one word, 'benign' or 'malicious'. If uncertain, take your best guess."
  )
  content = await query_via_websocket(secgemini_client, query)
  content = parse_secgemini_response(content)
  assert content == "malicious"


@pytest.mark.asyncio
@async_require_env_variable("SEC_GEMINI_API_KEY")
async def test_check_ws_messages_without_streaming(secgemini_client: SecGemini):
  query = "Tell me about CVE-2025-37991"
  api_key = os.environ["SEC_GEMINI_API_KEY"]
  session = secgemini_client.create_session()
  print(f"Session ID: {session.id}")

  messages = await get_messages_from_ws_query(
    secgemini_client, session.id, query, api_key, stream=False
  )

  # Stats for message_type
  result_num = 0
  thinking_num = 0
  info_num = 0
  error_num = 0
  other_num = 0
  # Stats for state
  end_num = 0
  # Stats for status_code
  partial_num = 0
  # Other stats
  info_end_num = 0
  transfer_to_agent_num = 0
  for message in messages:
    message.status_code
    if message.message_type == MessageType.RESULT:
      result_num += 1
    elif message.message_type == MessageType.THINKING:
      thinking_num += 1
    elif message.message_type == MessageType.INFO:
      info_num += 1
    elif message.message_type == MessageType.ERROR:
      error_num += 1
    else:
      other_num += 1

    if message.state == State.END:
      end_num += 1

    if message.status_code == ResponseStatus.PARTIAL_CONTENT.value:
      partial_num += 1

    if message.message_type == MessageType.INFO and message.state == State.END:
      info_end_num += 1

    if (
      message.message_type == MessageType.INFO and message.content == "Transfer"
    ):
      transfer_to_agent_num += 1

  assert result_num == 1
  assert thinking_num > 0
  assert info_num > 0
  assert error_num == 0
  assert other_num == 0
  assert end_num == 1
  assert partial_num == 0
  assert info_end_num == 1
  assert transfer_to_agent_num > 0
  print("OK")


async def get_messages_from_ws_query(
  secgemini_client: SecGemini,
  session_id: str,
  query: str,
  api_key: str,
  stream: bool,
) -> list[Message]:
  msg = Message(
    id=session_id,
    parent_id=ROOT_ID,
    role=Role.USER,
    mime_type=MimeType.TEXT,
    message_type=MessageType.QUERY,
    content=query,
  )

  uri = f"{secgemini_client.base_websockets_url}/v1/stream?api_key={api_key}&session_id={session_id}"
  if stream:
    uri += "&stream=1"
  messages: list[Message] = []
  async with websockets.connect(uri) as websocket:
    print(f"Sending message {msg}")
    await websocket.send(msg.model_dump_json())

    try:
      while True:
        received_msg = Message(
          **json.loads(await asyncio.wait_for(websocket.recv(), timeout=60))
        )
        print(f"Received message: {received_msg}")
        messages.append(received_msg)
        if (
          received_msg.message_type == MessageType.INFO
          and received_msg.state == State.END
        ):
          break
        if received_msg.status_code != ResponseStatus.OK:
          break
    except asyncio.TimeoutError:
      print("Reached timeout without having received a State.END message")
      raise
    except Exception:
      print(
        f"Exception while sending/receiving messages. {traceback.format_exc()}"
      )
      raise

  return messages


async def query_via_websocket(secgemini_client: SecGemini, query: str) -> str:
  session = secgemini_client.create_session()

  api_key = os.environ["SEC_GEMINI_API_KEY"]
  session_id = session.id

  msg = Message(
    id=session.id,
    parent_id="3713",
    role=Role.USER,
    mime_type=MimeType.TEXT,
    message_type=MessageType.QUERY,
    content=query,
  )

  uri = f"{secgemini_client.base_websockets_url}/v1/stream?api_key={api_key}&session_id={session_id}"
  async with websockets.connect(uri) as websocket:
    await websocket.send(msg.model_dump_json())

    result_msg = ""
    try:
      while True:
        received_msg = Message(
          **json.loads(await asyncio.wait_for(websocket.recv(), timeout=30))
        )
        print(received_msg.model_dump())

        if received_msg.message_type == MessageType.RESULT:
          assert received_msg.content is not None
          result_msg += received_msg.content
        if (
          received_msg.message_type == MessageType.INFO
          and received_msg.state == State.END
        ):
          break
    except asyncio.TimeoutError:
      print("Reached timeout without having received a State.END message")
      raise
    except Exception:
      print(
        f"Exception while sending/receiving messages. {traceback.format_exc()}"
      )
      raise
  return result_msg
