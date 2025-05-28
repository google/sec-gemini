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

import pytest
from sec_gemini import SecGemini
from sec_gemini.models.modelinfo import ModelInfo
from sec_gemini.session import InteractiveSession


def test_user_info_is_received_correctly(secgemini_client, mock_user, httpx_mock):
    httpx_mock.add_response(
        url=secgemini_client.base_url + "/v1/user/info", json=mock_user.model_dump()
    )
    info = secgemini_client.get_info()
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


def test_get_stable_model(secgemini_client_with_models, mock_stable_model_info):
    stable_model = secgemini_client_with_models.get_stable_model()
    assert stable_model is not None
    assert isinstance(stable_model, ModelInfo)
    assert stable_model.model_string == mock_stable_model_info.model_string
    assert not stable_model.is_experimental


def test_get_experimental_model(
    secgemini_client_with_models, mock_experimental_model_info
):
    experimental_model = secgemini_client_with_models.get_experimental_model()
    assert experimental_model is not None
    assert isinstance(experimental_model, ModelInfo)
    assert experimental_model.model_string == mock_experimental_model_info.model_string
    assert experimental_model.is_experimental


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_resume_session(secgemini_client_with_models, httpx_mock, mock_public_session):
    httpx_mock.add_response(
        url=f"http://localhost:8000/v1/session/get?session_id={mock_public_session.id}",
        method="GET",
        json=mock_public_session.model_dump(),
    )
    session = secgemini_client_with_models.resume_session(
        session_id=mock_public_session.id
    )
    assert session is not None
    assert isinstance(session, InteractiveSession)
    assert session.id == mock_public_session.id


@pytest.mark.httpx_mock
def test_create_session_invalid_model_name(secgemini_client_with_models):
    with pytest.raises(
        ValueError,
        match="Invalid model name invalid_model - must be 'stable' or 'experimental'.",
    ):
        secgemini_client_with_models.create_session(model="invalid_model")


@pytest.mark.httpx_mock
def test_create_session_invalid_model_type(secgemini_client_with_models):
    with pytest.raises(
        ValueError, match="Invalid model 123 - must be a ModelInfo object."
    ):
        secgemini_client_with_models.create_session(model=123)  # type: ignore


def test_init_no_api_key():
    with pytest.raises(ValueError, match="API key required"):
        SecGemini(
            api_key="",
            base_url="http://localhost:8000",
            base_websockets_url="ws://localhost:8000",
        )


def test_init_invalid_base_url(mock_user_info_with_models):
    with pytest.raises(ValueError, match="Invalid base_url"):
        SecGemini(
            api_key="test_key",
            base_url="invalid_url",
            base_websockets_url="ws://localhost:8000",
        )


def test_init_invalid_websockets_url(mock_user_info_with_models):
    with pytest.raises(ValueError, match="Invalid base_websockets_url"):
        SecGemini(
            api_key="test_key",
            base_url="http://localhost:8000",
            base_websockets_url="invalid_ws_url",
        )


@pytest.mark.httpx_mock
def test_init_get_info_fails(httpx_mock):
    httpx_mock.add_response(
        url="http://localhost:8000/v1/user/info", method="GET", status_code=500
    )
    with pytest.raises(ValueError, match="API Key is invalid or the API is down."):
        print("hi")
        SecGemini(
            api_key="test_key",
            base_url="http://localhost:8000",
            base_websockets_url="ws://localhost:8000",
        )


@pytest.mark.httpx_mock
def test_get_info_request_error(secgemini_client_with_models, httpx_mock):
    # secgemini_client_with_models fixture mocks a successful get_info for __init__.
    # We need a new mock for a subsequent call to get_info that fails.
    httpx_mock.add_response(
        url="http://localhost:8000/v1/user/info",
        method="GET",
        status_code=401,  # Simulate an authorization error for example
        json={
            "detail": "Authentication credentials were not provided or were invalid."
        },
    )
    user_info = secgemini_client_with_models.get_info()
    assert user_info is None
