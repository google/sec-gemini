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

use std::cmp::Ordering;

use reqwest::Client;
use reqwest::header::HeaderMap;
use semver::Version;
use serde::Deserialize;

use crate::util::{USER_AGENT, insert_static};

#[derive(clap::Args)]
pub struct Action {
    /// Only prints the release page URL instead of opening it.
    #[arg(long)]
    print: bool,
}

impl Action {
    pub async fn run(self) {
        let Some(url) = self.fetch().await else {
            println!("The CLI is up-to-date.");
            return;
        };
        println!("A new version of the CLI is available.");
        if self.print || opener::open_browser(&url).is_err() {
            println!("You can download it from {url}");
        }
    }

    async fn fetch(&self) -> Option<String> {
        let mut headers = HeaderMap::new();
        insert_static(&mut headers, reqwest::header::ACCEPT, "application/vnd.github+json");
        insert_static(&mut headers, "x-github-api-version", "2022-11-28");
        let client = try_to!(
            "build HTTP client",
            Client::builder().user_agent(&*USER_AGENT).default_headers(headers).build(),
        );
        let mut next_page =
            Some("https://api.github.com/repos/google/sec-gemini/releases".to_string());
        let current = Version::parse(env!("CARGO_PKG_VERSION")).unwrap();
        log::debug!("Searching against {current}");
        while let Some(url) = next_page {
            log::debug!("Fetching {url}");
            let response = try_to!(
                "fetch next release page",
                client.get(url).send().await.and_then(|x| x.error_for_status()),
            );
            next_page = response.headers().get(reqwest::header::LINK).and_then(|link| {
                let link = try_to!("parse link header", link.to_str());
                for x in link.split(", ") {
                    let (url, rel) = try_to!("split link header", x.split_once("; "));
                    if rel != r#"rel="next""# {
                        continue;
                    }
                    let url = try_to!(
                        "extract link url",
                        url.strip_prefix("<").and_then(|x| x.strip_suffix(">")),
                    );
                    return Some(url.to_string());
                }
                None
            });
            for release in try_to!("parse response", response.json::<Vec<Release>>().await) {
                let Some(version) = release.tag_name.strip_prefix("cli-v") else { continue };
                let version = try_to!("parse release version", Version::parse(version));
                log::debug!("Checking {version}");
                match current.cmp_precedence(&version) {
                    Ordering::Less => return Some(release.html_url),
                    Ordering::Equal => return None,
                    Ordering::Greater => (),
                }
            }
        }
        fail!("failed to find the current release")
    }
}

#[derive(Debug, Deserialize)]
struct Release {
    html_url: String,
    tag_name: String,
}
