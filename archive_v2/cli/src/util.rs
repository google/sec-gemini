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

use std::io::ErrorKind;
use std::path::Path;
use std::sync::LazyLock;

use platform_info::{PlatformInfoAPI, UNameAPI};
use rand::Rng;
use reqwest::header::{HeaderMap, HeaderValue, IntoHeaderName};
use uuid::Uuid;

pub static USER_AGENT: LazyLock<String> = LazyLock::new(|| {
    let name = env!("CARGO_PKG_NAME");
    let version = env!("CARGO_PKG_VERSION");
    let info = platform_info::PlatformInfo::new().unwrap();
    let sysname = info.sysname().display();
    let machine = info.machine().display();
    format!("{name}/{version} ({sysname} {machine})")
});

pub fn insert_static(headers: &mut HeaderMap, key: impl IntoHeaderName, value: &'static str) {
    assert!(headers.insert(key, HeaderValue::from_static(value)).is_none());
}

pub fn choose<T>(xs: &[T]) -> &T {
    &xs[rand::rng().random_range(0 .. xs.len())]
}

pub async fn read_file(path: impl AsRef<Path>) -> std::io::Result<Option<Vec<u8>>> {
    let path = path.as_ref();
    log::debug!("Reading {}", path.display());
    match tokio::fs::read(path).await {
        Ok(x) => Ok(Some(x)),
        Err(e) if e.kind() == ErrorKind::NotFound => Ok(None),
        Err(e) => Err(e),
    }
}

pub async fn remove_file(path: impl AsRef<Path>) -> std::io::Result<()> {
    let path = path.as_ref();
    log::debug!("Deleting {}", path.display());
    match tokio::fs::remove_file(path).await {
        Ok(()) => Ok(()),
        Err(e) if e.kind() == ErrorKind::NotFound => Ok(()),
        Err(e) => Err(e),
    }
}

pub fn uuid4() -> String {
    Uuid::new_v4().as_simple().to_string()
}

pub fn uuid4_short() -> String {
    format!("{:.12x}", Uuid::new_v4().as_simple())
}
