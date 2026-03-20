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

import logging

from rich.logging import RichHandler

_LOGGER = None


def get_logger():
  global _LOGGER
  if _LOGGER is None:
    _LOGGER = logging.getLogger("secgemini")
    _LOGGER.setLevel(level=logging.WARNING)

    rich_handler = RichHandler(
      show_time=True,  # Ensure timestamp is shown
      show_path=False,  # Hides file path for a cleaner log
    )

    _LOGGER.addHandler(rich_handler)

    _LOGGER.propagate = False

  return _LOGGER
