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


import os
import time

import pytest
from pytest_httpx import HTTPXMock
from utils import require_env_variable

from sec_gemini import SecGemini
from sec_gemini.models.enums import State, UserType
from sec_gemini.models.modelinfo import ModelInfo, OptionalToolSet, ToolSetVendor
from sec_gemini.models.public import (
    PublicSession,
    PublicUser,
    PublicUserVendor,
    UserInfo,
)
from sec_gemini.models.usage import Usage

MOCK_SEC_GEMINI_API_HOST = "api.secgemini.google-mock"
MOCK_SEC_GEMINI_API_KEY = "p9XXXXMOCKKEYXXXX"


@pytest.fixture
def mock_user(
    mock_stable_model_info: ModelInfo, mock_experimental_model_info: ModelInfo
) -> UserInfo:
    """Provides a mock user object for testing."""

    vendor = PublicUserVendor(
        name="TestVendor",
        description="A test vendor",
        url="http://testvendor.com",
        svg="<svg>...</svg>",
    )

    return UserInfo(
        user=PublicUser(
            id="test-user-id",
            org_id="test-org-id",
            type=UserType.USER,
            never_log=False,
            can_disable_logging=True,
            key_expire_time=1699999999,
            tpm=1000,
            rpm=1000,
            allow_experimental=True,
            vendors=[vendor],
        ),
        sessions=[],
        available_models=[
            mock_stable_model_info,
            mock_experimental_model_info,
        ],
    )


@pytest.fixture
def mock_stable_model_info() -> ModelInfo:
    """Provides a mock stable ModelInfo object."""
    vendor = ToolSetVendor(
        name="TestVendor",
        description="A test vendor",
        url="http://testvendor.com",
        svg="<svg>...</svg>",
    )
    return ModelInfo(
        model_name="sec-gemini",
        version="1",
        use_experimental=False,
        model_string="sec-gemini-1.1",
        toolsets=[
            OptionalToolSet(
                name="TestToolset",
                version=1,
                description="A test toolset",
                vendor=vendor,
                is_enabled=True,
                is_experimental=False,
            )
        ],
    )


@pytest.fixture
def mock_experimental_model_info() -> ModelInfo:
    """Provides a mock experimental ModelInfo object."""
    vendor = ToolSetVendor(
        name="TestVendor",
        description="A test vendor",
        url="http://testvendor.com",
        svg="<svg>...</svg>",
    )
    return ModelInfo(
        model_name="sec-gemini",
        version="1",
        use_experimental=True,
        model_string="sec-gemini-1.1-experimental",
        toolsets=[
            OptionalToolSet(
                name="TestToolset",
                version=1,
                description="A test toolset",
                vendor=vendor,
                is_enabled=True,
                is_experimental=True,
            )
        ],
    )


@pytest.fixture
def mock_public_session(mock_stable_model_info: ModelInfo) -> PublicSession:
    """Provides a mock PublicSession object."""

    usage = Usage(
        total_tokens=100,
        prompt_tokens=50,
        generated_tokens=50,
        cached_token_count=0,
        thoughts_token_count=0,
        tool_use_prompt_token_count=0,
    )

    return PublicSession(
        id="test-session-id",
        user_id="test-user-id",
        org_id="test-org-id",
        model=mock_stable_model_info,
        ttl=3600,
        language="en",
        turns=0,
        name="Test Session",
        description="A test session",
        create_time=int(time.time()),
        update_time=int(time.time()),
        num_messages=0,
        messages=[],
        usage=usage,
        can_log=True,
        state=State.START,
        files=[],
    )


@pytest.fixture
@require_env_variable("SEC_GEMINI_API_KEY")
def secgemini_client() -> SecGemini:
    """Provides a SecGemini client for testing.

    It uses the SEC_GEMINI_API_HOST env variable to determine the SecGemini's
    API host. If the env variable is not defined, it uses the real SecGemini's
    API endpoint.
    """

    api_key = os.getenv("SEC_GEMINI_API_KEY", "").strip()
    if api_key == "":
        raise Exception(
            "Could not find a valid key in the SEC_GEMINI_API_KEY env variable"
        )

    return SecGemini(api_key=api_key)


@pytest.fixture
def mock_secgemini_client(httpx_mock: HTTPXMock, mock_user: UserInfo) -> SecGemini:
    """Provides a mock SecGemini client for testing."""
    httpx_mock.add_response(
        url=f"http://{MOCK_SEC_GEMINI_API_HOST}:8000/v1/user/info",
        method="GET",
        json=mock_user.model_dump(),
    )
    base_url = f"http://{MOCK_SEC_GEMINI_API_HOST}:8000"
    wss_url = f"ws://{MOCK_SEC_GEMINI_API_HOST}:8000"
    return SecGemini(
        api_key=MOCK_SEC_GEMINI_API_KEY, base_url=base_url, base_websockets_url=wss_url
    )
