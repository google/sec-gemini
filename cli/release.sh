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

[ -z "$(git status -s)" ] || error "Repository is not clean"

VERSION="$(sed -n '3s/^## //p' CHANGELOG.md)"
[ "${VERSION%-git}" = "$VERSION" ] && success "Nothing to release"

info "Removing all -git suffixes"
sed -i 's/-git//' Cargo.* CHANGELOG.md
VERSION="${VERSION%-git}"

info "Reset CHANGELOG.md counter"
sed -i 's/\(^<!-- .* test\): [0-9]* -->$/\1: 0 -->/' CHANGELOG.md

info "Updating README.md"
sed -i 's#\(releases/tag/cli/sec-gemini-v\).*$#\1'"$VERSION"'#' README.md

info "Creating a commit with those changes"
git commit -aqm"Release CLI v$VERSION"

todo "Create a PR with this commit, merge it, and tag it cli/sec-gemini-v$VERSION"
