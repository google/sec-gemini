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

use reqwest::header::{HeaderMap, HeaderValue};
use serde::Serialize;
use serde::de::DeserializeOwned;

use crate::cli::FLAGS;

pub struct Client {
    inner: reqwest::Client,
}

impl Client {
    pub fn new() -> Self {
        let api_key = FLAGS.api_key().to_string();
        let mut headers = HeaderMap::new();
        let Ok(mut api_key_value) = HeaderValue::from_str(&api_key) else {
            fail!("The Sec-Gemini API key is malformed.")
        };
        api_key_value.set_sensitive(true);
        assert!(headers.insert("x-api-key", api_key_value).is_none());
        let content_type = HeaderValue::from_static("application/json");
        assert!(headers.insert("Content-Type", content_type).is_none());
        let inner = match reqwest::Client::builder().default_headers(headers).build() {
            Ok(x) => x,
            Err(e) => fail!("Failed to build HTTP client: {e}"),
        };
        Client { inner }
    }

    pub async fn get<T: DeserializeOwned>(
        &self, path: &str, query: Option<&str>,
    ) -> reqwest::Result<T> {
        let mut url = FLAGS.base_url.clone();
        url.set_path(path);
        url.set_query(query);
        self.inner.get(url).send().await?.error_for_status()?.json().await
    }

    pub async fn post<T: Serialize + ?Sized, R: DeserializeOwned>(
        &self, path: &str, body: &T,
    ) -> reqwest::Result<R> {
        let mut url = FLAGS.base_url.clone();
        url.set_path(path);
        self.inner.post(url).json(body).send().await?.error_for_status()?.json().await
    }
}
