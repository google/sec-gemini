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


def test_user_info_is_received_correctly(secgemini_client, mock_user, httpx_mock):
    httpx_mock.add_response(
        url=secgemini_client.base_url + "/v1/user/info",
        json=mock_user.model_dump()
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

