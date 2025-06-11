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

PYTHON=../sec-gemini-python/sec_gemini/session.py
RUST=src/cli/interact/name.rs

match() { echo '/^ *'$1' = \[/,/^ *\]/p'; }
subst() { echo 's/'$1' = /pub const '$2': \&[\&str] = \&/'; }
extract() {
  echo >> $RUST
  sed -n "$(match $1)" $PYTHON | sed "$(subst $1 $2)" >> $RUST
  echo ';' >> $RUST
}

sed -n '1,/^$/p' src/cli/interact.rs > $RUST
extract adjs ADJS
extract terms TERMS
rustfmt $RUST
