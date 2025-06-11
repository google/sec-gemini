// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use rand::Rng;
use reqwest::header::{HeaderMap, HeaderValue, IntoHeaderName};

pub const USER_AGENT: &str = concat!(env!("CARGO_PKG_NAME"), "/", env!("CARGO_PKG_VERSION"));

pub fn insert_static(headers: &mut HeaderMap, key: impl IntoHeaderName, value: &'static str) {
    assert!(headers.insert(key, HeaderValue::from_static(value)).is_none());
}

pub fn choose<T>(xs: &[T]) -> &T {
    &xs[rand::rng().random_range(0 .. xs.len())]
}
