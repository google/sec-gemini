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
from sec_gemini.models.public import UserInfo, PublicUser

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
def secgemini_client(httpx_mock, mock_user):
    """Provides a mock SecGemini client for testing."""
    httpx_mock.add_response(
        json=mock_user.model_dump()
    )
    BASE_URL = 'http://localhost:8000' 
    WSS_URL = 'ws://localhost:8000'
    API_KEY = 'test-key-fixture'
    return SecGemini(api_key=API_KEY,
                    base_url=BASE_URL,
                   base_websockets_url=WSS_URL)