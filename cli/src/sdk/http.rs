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
use url::Url;

use crate::config;
use crate::util::{USER_AGENT, insert_static};

pub struct Client {
    pub base_url: Url,
    inner: reqwest::Client,
}

impl Client {
    pub async fn new(api_key: &str) -> Self {
        let base_url = config::BASE_URL.get().await.0;
        let mut headers = HeaderMap::new();
        insert_static(&mut headers, "x-sdk-version", env!("CARGO_PKG_VERSION"));
        insert_static(&mut headers, "x-sdk", "rust");
        insert_api_key(&mut headers, api_key);
        insert_static(&mut headers, reqwest::header::CONTENT_TYPE, "application/json");
        let inner = try_to!(
            "build HTTP client",
            reqwest::Client::builder().user_agent(USER_AGENT).default_headers(headers).build(),
        );
        Client { base_url, inner }
    }

    pub async fn get<T: DeserializeOwned>(
        &self, path: &str, query: Option<&str>,
    ) -> reqwest::Result<T> {
        let mut url = self.base_url.clone();
        url.set_path(path);
        url.set_query(query);
        self.inner.get(url).send().await?.error_for_status()?.json().await
    }

    pub async fn post<T: Serialize + ?Sized, R: DeserializeOwned>(
        &self, path: &str, body: &T,
    ) -> reqwest::Result<R> {
        let mut url = self.base_url.clone();
        url.set_path(path);
        self.inner.post(url).json(body).send().await?.error_for_status()?.json().await
    }
}

fn insert_api_key(headers: &mut HeaderMap, api_key: &str) {
    let Ok(mut api_key) = HeaderValue::from_str(api_key) else {
        fail!("the Sec-Gemini API key is malformed")
    };
    api_key.set_sensitive(true);
    assert!(headers.insert("x-api-key", api_key).is_none());
}
