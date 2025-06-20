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
use futures_util::stream::SplitSink;
use futures_util::{SinkExt, StreamExt};
use reqwest::StatusCode;
use tokio::net::TcpStream;
use tokio::sync::mpsc::{UnboundedReceiver, unbounded_channel};
use tokio::sync::{Mutex, MutexGuard};
use tokio::task::AbortHandle;
use tokio_tungstenite::{MaybeTlsStream, WebSocketStream};

use self::types::*;
use crate::util::choose;
use crate::{StrError, config, fail, or_fail};

mod http;
mod name;
pub mod types;

pub struct Sdk {
    api_key: String,
    http: http::Client,
    user: PublicUser,
    sessions: Mutex<Vec<PublicSession>>,
    model: ModelInfo,
}

pub struct Session {
    id: String,
    sdk: Arc<Sdk>,
    state: Option<SessionState>,
}

impl Sdk {
    pub async fn new(interactive: bool) -> Self {
        let (http, api_key, UserInfo { user, sessions, available_models }) = loop {
            let (api_key, source) = config::API_KEY.get().await;
            let http = http::Client::new(&api_key).await;
            let info = match http.get::<UserInfo>("/v1/user/info", None).await {
                Ok(user_info) => {
                    config::API_KEY.persist().await;
                    user_info
                }
                Err(error) => {
                    let instr: Option<&dyn Display> = match error.status() {
                        Some(StatusCode::UNAUTHORIZED | StatusCode::FORBIDDEN) => {
                            if source == config::Source::File {
                                config::API_KEY.set_term();
                                continue;
                            }
                            Some(&"Please check your API key.")
                        }
                        _ => None,
                    };
                    fail("failed to get user info", Some(&error), instr);
                }
            };
            break (http, api_key, info);
        };
        if interactive {
            println!("User: {} ({})", user.id.blue(), user.org_id.purple());
        }
        for model in available_models {
            if model.use_experimental {
                continue;
            }
            if interactive {
                println!("Model: {}", model.model_string.green());
            }
            let sessions = Mutex::new(sessions);
            return Sdk { api_key, http, user, sessions, model };
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

    async fn session_get(&self, id: &str) -> PublicSession {
        or_fail(self.http.get("/v1/session/get", Some(&format!("session_id={id}"))).await)
    }

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
            fail!("failed to create session", &StrError(result.status_message));
        }
        log::info!("{}", result.status_message);
        let id = session.id.clone();
        sdk.cached_sessions().await.push(session);
        Session { id, sdk, state: None }
    }

    pub fn resume(sdk: Arc<Sdk>, id: String) -> Session {
        Session { id, sdk, state: None }
    }

    pub async fn delete(sdk: &Sdk, id: &str) -> PublicSession {
        let session = sdk.session_get(id).await;
        let result = sdk.session_delete(&session).await;
        assert!(result.ok);
        log::info!("{}", result.status_message);
        session
    }

    pub async fn send(&mut self, prompt: &str) {
        let message = MessageBuilder::new(MessageType::Query)
            .mime_type(Some("text/plain".to_string()))
            .content(Some(prompt.to_string()))
            .build();
        let message = serde_json::to_string(&message).unwrap();
        try_to!(
            "send web-socket message",
            self.state().await.sink.send(tungstenite::Message::text(message)).await
        );
    }

    pub async fn recv(&mut self) -> Option<Message> {
        self.state().await.recv.recv().await
    }

    pub fn done(&mut self) {
        if let Some(state) = self.state.take() {
            state.abort.abort();
        }
    }

    async fn state(&mut self) -> &mut SessionState {
        if self.state.is_none() {
            let mut url = self.sdk.http.base_url.clone();
            url.set_scheme("wss").unwrap();
            url.set_path("/v1/stream");
            url.set_query(Some(&format!("api_key={}&session_id={}", self.sdk.api_key, self.id)));
            let (stream, _) = try_to!(
                "connect to Sec-Gemini web-socket",
                tokio_tungstenite::connect_async(url).await,
            );
            let (sink, mut stream) = stream.split();
            let (onmessage, msg_queue) = unbounded_channel::<Message>();
            let abort = tokio::spawn(async move {
                while let Some(message) = stream.next().await {
                    let message = match try_to!("receive web-socket message", message) {
                        tungstenite::Message::Text(x) => x,
                        tungstenite::Message::Ping(_) => continue, // handled by tungstenite
                        x => fail!("received unexpected web-socket message {x:?}"),
                    };
                    log::trace!("received {message}");
                    match onmessage.send(try_to!(
                        "parse web-socket message",
                        serde_json::from_str(message.as_str())
                    )) {
                        Ok(()) => (),
                        Err(_) => break,
                    }
                }
            })
            .abort_handle();
            self.state = Some(SessionState { recv: msg_queue, sink, abort })
        }
        self.state.as_mut().unwrap()
    }
}

struct SessionState {
    recv: UnboundedReceiver<Message>,
    sink: SplitSink<WebSocketStream<MaybeTlsStream<TcpStream>>, tungstenite::Message>,
    abort: AbortHandle,
}
