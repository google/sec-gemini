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
from sec_gemini.models.public import UserInfo, PublicUser, PublicSession
from sec_gemini.models.modelinfo import ModelInfo, ModelSubAgentInfo
from sec_gemini.models.enums import State
from sec_gemini.models.usage import Usage
from sec_gemini.models.message import Message
import time

@pytest.fixture
def mock_user():
    """Provides a mock user object for testing."""
    return  UserInfo(
        user=PublicUser(
            id="test-user-id",
            org_id="test-org-id",
            type="user",
            never_log=False,
            can_disable_logging=True,
            key_expire_time=1699999999,
            tpm=1000,
            rpm=1000,
            allow_experimental=True,
            vendors=["vendor1", "vendor2"],
        ),
        sessions=[],
        available_models=[],
    )

@pytest.fixture
def mock_stable_model_info():
    """Provides a mock stable ModelInfo object."""
    return ModelInfo(
        model_string="stable-model-v1",
        is_experimental=False,
                version='1',
        subagents=[
            ModelSubAgentInfo(
                name="StableAgent",
                vendor="TestVendor",
                version="1.0",
                is_enabled=True,
                is_optional=False,
                is_experimental=False,
                description="A stable test agent",
            )
        ],
    )

@pytest.fixture
def mock_experimental_model_info():
    """Provides a mock experimental ModelInfo object."""
    return ModelInfo(
        model_string="experimental-model-v2",
        is_experimental=True,
        version='1',
        subagents=[
            ModelSubAgentInfo(
                name="ExperimentalAgent",
                vendor="TestVendor",
                version="2.0",
                is_enabled=True,
                is_optional=False,
                is_experimental=True,
                description="An experimental test agent",
            )
        ],
    )

@pytest.fixture
def mock_user_info_with_models(mock_user, mock_stable_model_info, mock_experimental_model_info):
    """Provides a mock UserInfo object that includes available models."""
    user_info = mock_user
    user_info.available_models = [mock_stable_model_info, mock_experimental_model_info]
    return user_info

@pytest.fixture
def mock_public_session(mock_stable_model_info: ModelInfo):
    """Provides a mock PublicSession object."""
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
        usage=Usage(),
        can_log=True,
        state=State.START,
        files=[],
    )

@pytest.fixture
def secgemini_client(httpx_mock, mock_user):
    """Provides a mock SecGemini client for testing."""
    httpx_mock.add_response(
        url="http://localhost:8000/v1/user/info", # Ensure this matches the actual endpoint used by get_info in __init__
        method="GET",
        json=mock_user.model_dump()
    )
    BASE_URL = 'http://localhost:8000' 
    WSS_URL = 'ws://localhost:8000'
    API_KEY = 'test-key-fixture'
    return SecGemini(api_key=API_KEY,
                    base_url=BASE_URL,
                   base_websockets_url=WSS_URL)

@pytest.fixture
def secgemini_client_with_models(httpx_mock, mock_user_info_with_models):
    """Provides a mock SecGemini client, ensuring get_info returns models."""
    httpx_mock.add_response(
        url="http://localhost:8000/v1/user/info", # Ensure this matches the actual endpoint used by get_info
        method="GET",
        json=mock_user_info_with_models.model_dump()
    )
    BASE_URL = 'http://localhost:8000'
    WSS_URL = 'ws://localhost:8000'
    API_KEY = 'test-key-fixture'
    client = SecGemini(api_key=API_KEY,
                       base_url=BASE_URL,
                       base_websockets_url=WSS_URL)
    # Ensure the client's models are set up based on the mocked get_info response
    client.stable_model = mock_user_info_with_models.available_models[0]
    client.experimental_model = mock_user_info_with_models.available_models[1]
    return client