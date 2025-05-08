#!/bin/sh
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

set -e

echo "Running unit tests"
./test.sh

echo "Formatting toml files"
env RUST_LOG=warn taplo format

echo "Checking for modified files"
git diff --exit-code

echo "Checking for untracked files"
[ -z "$(git status -s)" ] || { git status -s; false; }
