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

use std::fmt::Display;
use std::sync::Arc;

use colored::Colorize;
use futures_util::{SinkExt, StreamExt};
use reqwest::StatusCode;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender, unbounded_channel};
use tokio::sync::{Mutex, MutexGuard};
use url::Url;

use self::types::*;
use crate::config::Config;
use crate::util::choose;
use crate::{StrError, fail, or_fail, try_to};

mod http;
mod name;
pub mod types;

pub struct Options {
    pub api_key: Config,
    pub base_url: Url,
    pub interactive: bool,
}

pub struct Sdk {
    options: Options,
    http: http::Client,
    user: PublicUser,
    sessions: Mutex<Vec<PublicSession>>,
    model: ModelInfo,
}

pub struct Session {
    id: String,
    recv: UnboundedReceiver<Message>,
    send: UnboundedSender<tungstenite::Message>,
}

impl Sdk {
    pub async fn new(mut options: Options) -> Self {
        let mut bypass = false;
        let (http, UserInfo { user, sessions, available_models }) = loop {
            options.api_key.force(bypass);
            let http = http::Client::new(&options);
            let info = match http.get::<UserInfo>("/v1/user/info", None).await {
                Ok(user_info) => {
                    options.api_key.persist();
                    user_info
                }
                Err(error) => {
                    let instr: Option<&dyn Display> = match error.status() {
                        Some(StatusCode::UNAUTHORIZED | StatusCode::FORBIDDEN) => {
                            if !bypass && options.api_key.reset() {
                                bypass = true;
                                continue;
                            }
                            Some(&"Please check your API key.")
                        }
                        _ => None,
                    };
                    fail("failed to get user info", Some(&error), instr);
                }
            };
            break (http, info);
        };
        if options.interactive {
            println!("User: {} ({})", user.id.blue(), user.org_id.purple());
        }
        for model in available_models {
            if model.use_experimental {
                continue;
            }
            if options.interactive {
                println!("Model: {}", model.model_string.green());
            }
            let sessions = Mutex::new(sessions);
            return Sdk { options, http, user, sessions, model };
        }
        fail!("no stable model found")
    }

    pub async fn cached_sessions(&self) -> MutexGuard<'_, Vec<PublicSession>> {
        self.sessions.lock().await
    }

    pub async fn refresh_sessions(&self) {
        let info = try_to!("list sessions", self.http.get::<UserInfo>("/v1/user/info", None).await);
        *self.sessions.lock().await = info.sessions;
    }

    async fn session_register(&self, session: &PublicSession) -> OpResult {
        or_fail(self.http.post("/v1/session/register", session).await)
    }

    #[allow(dead_code)]
    async fn session_get(&self, id: &str) -> PublicSession {
        or_fail(self.http.get("/v1/session/get", Some(&format!("session_id={id}"))).await)
    }

    #[allow(dead_code)]
    async fn session_delete(&self, session: &PublicSession) -> OpResult {
        or_fail(self.http.post("/v1/session/delete", session).await)
    }
}

impl Session {
    pub fn id(&self) -> &str {
        &self.id
    }

    pub async fn new(sdk: Arc<Sdk>, mut name: String) -> Session {
        if name.is_empty() {
            name = format!("{}-{}", choose(name::ADJS), choose(name::TERMS));
            println!("Session: {}", name.cyan());
        }
        let session = PublicSessionBuilder::new(
            sdk.user.id.clone(),
            sdk.user.org_id.clone(),
            sdk.model.clone(),
            86400,
            name,
            "no description".to_string(),
        )
        .can_log(!sdk.user.never_log)
        .build();
        let result = sdk.session_register(&session).await;
        if !result.ok {
            fail!("failed to create session", &StrError(&result.status_message));
        }
        log::info!("{}", result.status_message);
        let id = session.id.clone();
        sdk.cached_sessions().await.push(session);
        Self::create(&sdk, id).await
    }

    pub async fn resume(sdk: &Sdk, id: String) -> Session {
        Self::create(sdk, id).await
    }

    async fn create(sdk: &Sdk, id: String) -> Session {
        let mut url = sdk.options.base_url.clone();
        url.set_scheme("wss").unwrap();
        url.set_path("/v1/stream");
        url.set_query(Some(&format!("api_key={}&session_id={id}", &*sdk.options.api_key)));
        let (stream, _) = try_to!(
            "connect to Sec-Gemini web-socket",
            tokio_tungstenite::connect_async(url).await,
        );
        let (mut sink, mut stream) = stream.split();
        let (onmessage, msg_queue) = unbounded_channel::<Message>();
        drop(tokio::spawn(async move {
            while let Some(message) = stream.next().await {
                let message = match try_to!("receive web-socket message", message) {
                    tungstenite::Message::Text(x) => x,
                    tungstenite::Message::Ping(_) => continue, // handled by tungstenite
                    x => fail!("received unexpected web-socket message {x:?}"),
                };
                log::trace!("received {message}");
                match onmessage.send(serde_json::from_str(message.as_str()).unwrap()) {
                    Ok(()) => (),
                    Err(_) => break,
                }
            }
        }));
        let (send, mut recv) = unbounded_channel::<tungstenite::Message>();
        drop(tokio::spawn(async move {
            while let Some(message) = recv.recv().await {
                try_to("send web-socket message", sink.send(message).await, None);
            }
        }));
        Session { id, recv: msg_queue, send }
    }

    #[allow(dead_code)]
    pub async fn delete(sdk: &Sdk, id: &str) -> PublicSession {
        let session = sdk.session_get(id).await;
        let result = sdk.session_delete(&session).await;
        assert!(result.ok);
        log::info!("{}", result.status_message);
        session
    }

    pub fn send(&self, prompt: &str) {
        let message = MessageBuilder::new(MessageType::Query)
            .mime_type(Some("text/plain".to_string()))
            .content(Some(prompt.to_string()))
            .build();
        let message = serde_json::to_string(&message).unwrap();
        try_to!("send web-socket message", self.send.send(tungstenite::Message::text(message)));
    }

    pub async fn recv(&mut self) -> Option<Message> {
        self.recv.recv().await
    }
}
