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

from .secgemini import SecGemini
from .test_fixtures import secgeminicli


def test_user_info(secgemini: SecGemini):
    ui = secgeminicli.get_info()
    assert ui is not None
    assert ui.user is not None
    assert ui.user.org_id is not None
    assert ui.user.type is not None
    assert ui.user.key_expire_time is not None

