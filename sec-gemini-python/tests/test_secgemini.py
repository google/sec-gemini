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


import json
import re

import httpx
import pytest
from conftest import MOCK_SEC_GEMINI_API_HOST
from pytest_httpx import HTTPXMock
from utils import parse_secgemini_response, require_env_variable

from sec_gemini import SecGemini
from sec_gemini.models.public import PublicSession, UserInfo
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
    session = mock_secgemini_client.resume_session(session_id=mock_public_session.id)
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
        "How much is 12345+54321? Just answer with the numeric value, nothing else."
    )
    content = resp.text().strip()
    assert content.find("66666") >= 0


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

    info = json.loads(content)
    assert "ips" in info.keys()
    assert len(info["ips"]) > 0
    for ip in info["ips"]:
        assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", ip)
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
def test_query_with_virustotat_tool_malicious(secgemini_client: SecGemini):
    session = secgemini_client.create_session()
    resp = session.query(
        "Is file a188ff24aec863479408cee54b337a2fce25b9372ba5573595f7a54b784c65f8 benign or malicious? "
        "Just output one word, 'benign' or 'malicious'. If uncertain, take your best guess."
    )
    content = resp.text().strip()
    content = parse_secgemini_response(content)
    assert content == "malicious"


@require_env_variable("SEC_GEMINI_API_KEY")
def test_query_with_attachment(secgemini_client: SecGemini):
    TEST_PDF_URL = "https://elie.net/static/files/retsim-resilient-and-efficient-text-similarity/retsim-resilient-and-efficient-text-similarity.pdf"
    pdf_content = httpx.get(TEST_PDF_URL).content

    session = secgemini_client.create_session()
    assert session.attach_file("paper.pdf", pdf_content) is True
    assert len(session.files) == 1

    resp = session.query(
        "The file in attachment should be about a tool in machine learning. What is the name of the tool?"
        "Just output one word, nothing else."
    )
    content = resp.text().strip()
    content = parse_secgemini_response(content)
    assert content.lower() == "retsim"


@require_env_variable("SEC_GEMINI_API_KEY")
def test_session_with_multiple_attachment(secgemini_client: SecGemini):
    TEST_PDF_URL = "https://elie.net/static/files/retsim-resilient-and-efficient-text-similarity/retsim-resilient-and-efficient-text-similarity.pdf"
    pdf_content = httpx.get(TEST_PDF_URL).content

    TEST_PYTHON_URL = "https://raw.githubusercontent.com/google/magika/refs/heads/main/tests_data/basic/python/code.py"
    python_content = httpx.get(TEST_PYTHON_URL).content

    session = secgemini_client.create_session()

    assert session.attach_file("paper.pdf", pdf_content) is True
    assert len(session.files) == 1
    assert session.attach_file("code.py", python_content) is True
    assert len(session.files) == 2
