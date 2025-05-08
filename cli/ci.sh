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
. ./color.sh

info "Checking CHANGELOG.md version"
x="$(sed -n '3s/^## //p' CHANGELOG.md)"
y="$(sed -n '3s/^version = "\(.*\)"/\1/p' Cargo.toml)"
[ -n "$x" ] || error "Missing version in CHANGELOG.md"
[ -n "$y" ] || error "Missing version in Cargo.toml"
[ "$x" = "$y" ] || error "Version mismatch between Cargo.toml and CHANGELOG.md"

info "Running unit tests"
./test.sh

info "Updating CLI output in README.md"
unset SEC_GEMINI_SHOW_THINKING
unset SEC_GEMINI_API_KEY
grep '^% sec-gemini ' README.md | while read line; do
  sed -i '/^'"$line"'$/,/```/{/^'"$line"'$/p;/```/!d}' README.md
  COLUMNS=89 cargo run -- ${line#% sec-gemini } </dev/null 2>/dev/null | sed 's/ *$//' > tmp
  sed -i '/^'"$line"'$/r tmp' README.md
done
rm tmp

info "Formatting toml files"
env RUST_LOG=warn taplo format

git diff --exit-code || error "Modified files"
[ -z "$(git status -s | tee /dev/stderr)" ] || error "Untracked files"
success "CI passed"
