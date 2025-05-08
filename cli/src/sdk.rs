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

use std::sync::Arc;

use futures_util::{SinkExt, StreamExt};
use tokio::sync::mpsc::{UnboundedSender, unbounded_channel};
use uuid::Uuid;

use self::types::*;
use crate::cli::FLAGS;
use crate::or_fail;

mod http;
pub mod types;

pub struct Sdk {
    http: http::Client,
    user: PublicUser,
    model: ModelInfoInput,
}

pub struct Session {
    send: UnboundedSender<tungstenite::Message>,
}

impl Sdk {
    pub async fn new() -> (Self, Vec<PublicSessionOutput>) {
        let http = http::Client::new();
        let UserInfo { user, sessions, available_models } = Sdk::user_info(&http).await;
        let sessions = sessions.unwrap_or_default();
        log::info!("User {} in org {}", user.id, user.org_id);
        let Some(available_models) = available_models else { fail!("No available models.") };
        for model in available_models {
            if model.is_experimental == Some(true) {
                continue;
            }
            log::info!("Using stable model {}", model.model_string);
            return (Sdk { http, user, model }, sessions);
        }
        fail!("No stable model found.")
    }

    async fn user_info(http: &http::Client) -> UserInfo {
        or_fail(http.get("/v1/user/info", None).await)
    }

    async fn session_register(&self, session: &PublicSessionOutput) -> OpResult {
        or_fail(self.http.post("/v1/session/register", session).await)
    }

    #[allow(dead_code)]
    async fn session_get(&self, id: &str) -> PublicSessionOutput {
        or_fail(self.http.get("/v1/session/get", Some(&format!("session_id={id}"))).await)
    }

    #[allow(dead_code)]
    async fn session_delete(&self, session: &PublicSessionOutput) -> OpResult {
        or_fail(self.http.post("/v1/session/delete", session).await)
    }
}

impl Session {
    pub async fn new(sdk: Arc<Sdk>, name: String, onmessage: UnboundedSender<Message>) -> Session {
        let can_log = match sdk.user.never_log {
            Some(true) => false,
            _ => true, // TODO: function parameter (check can_disable_logging)
        };
        let id = Uuid::new_v4().to_string();
        let session = PublicSessionInput {
            id: Some(id.clone()),
            user_id: sdk.user.id.clone(),
            org_id: sdk.user.org_id.clone(),
            model: sdk.model.clone(),
            ttl: 86400,
            name,
            description: "no description".to_string(), // TODO: function paramater
            can_log: Some(can_log),
            language: Some("en".to_string()),
            ..Default::default()
        };
        let result = sdk.session_register(&session).await;
        if !result.ok {
            let message = match result.status_message {
                Some(x) => format!(": {x}"),
                None => String::new(),
            };
            fail!("Failed to create session{message}");
        }
        if let Some(message) = result.status_message {
            log::info!("{message}");
        }
        Self::create(id, onmessage).await
    }

    pub async fn resume(id: String, onmessage: UnboundedSender<Message>) -> Session {
        Self::create(id, onmessage).await
    }

    async fn create(id: String, onmessage: UnboundedSender<Message>) -> Session {
        let mut url = FLAGS.base_url.clone();
        url.set_scheme("wss").unwrap();
        url.set_path("/v1/stream");
        url.set_query(Some(&format!("api_key={}&session_id={id}", FLAGS.api_key())));
        let (stream, _) = match tokio_tungstenite::connect_async(url).await {
            Ok(x) => x,
            Err(e) => fail!("Failed to connect to Sec-Gemini web-socket: {e}"),
        };
        let (mut sink, mut stream) = stream.split();
        drop(tokio::spawn(async move {
            while let Some(message) = stream.next().await {
                let message = match message {
                    Ok(tungstenite::Message::Text(x)) => x,
                    Ok(tungstenite::Message::Ping(_)) => continue, // handled by tungstenite
                    Ok(x) => fail!("Received unexpected web-socket message {x:?}"),
                    Err(e) => fail!("Failed to receive web-socket message: {e}"),
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
                match sink.send(message).await {
                    Ok(()) => (),
                    Err(e) => fail!("Failed to send web-socket message: {e}"),
                }
            }
        }));
        Session { send }
    }

    #[allow(dead_code)]
    pub async fn delete(sdk: &Sdk, id: &str) -> PublicSessionOutput {
        let session = sdk.session_get(id).await;
        let result = sdk.session_delete(&session).await;
        assert!(result.ok);
        if let Some(message) = result.status_message {
            log::info!("{message}");
        }
        session
    }

    pub fn send(&self, prompt: &str) {
        let message = Message {
            id: Some(Uuid::new_v4().to_string()),
            parent_id: Some("3713".to_string()),
            role: Some(Role::User),
            mime_type: Some(Some("text/plain".to_string())),
            message_type: MessageType::Query,
            content: Some(Some(prompt.to_string())),
            ..Default::default()
        };
        let message = serde_json::to_string(&message).unwrap();
        match self.send.send(tungstenite::Message::text(message)) {
            Ok(()) => (),
            Err(e) => fail!("Failed to send web-socket message: {e}"),
        }
    }
}
