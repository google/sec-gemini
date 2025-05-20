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
use reqwest::StatusCode;
use tokio::sync::mpsc::{UnboundedSender, unbounded_channel};
use url::Url;
use uuid::Uuid;

use self::types::*;
use crate::config::Config;
use crate::{or_fail, try_to};

mod http;
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
    model: ModelInfoInput,
}

pub struct Session {
    send: UnboundedSender<tungstenite::Message>,
}

impl Sdk {
    pub async fn new(mut options: Options) -> (Self, Vec<PublicSessionOutput>) {
        options.api_key.force();
        let http = http::Client::new(&options);
        let UserInfo { user, sessions, available_models } =
            match http.get::<UserInfo>("/v1/user/info", None).await {
                Ok(user_info) => {
                    options.api_key.persist();
                    user_info
                }
                Err(error) => {
                    options.api_key.delete();
                    let instr = match error.status() {
                        Some(StatusCode::UNAUTHORIZED | StatusCode::FORBIDDEN) => {
                            "\n\nPlease check your API key."
                        }
                        _ => "",
                    };
                    fail!("Failed to get user info: {error}{instr}");
                }
            };
        let sessions = sessions.unwrap_or_default();
        if options.interactive {
            println!("User: {} ({})", user.id, user.org_id);
        }
        let Some(available_models) = available_models else { fail!("No available models.") };
        for model in available_models {
            if model.is_experimental == Some(true) {
                continue;
            }
            if options.interactive {
                println!("Model: {}", model.model_string);
            }
            return (Sdk { options, http, user, model }, sessions);
        }
        fail!("No stable model found.")
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
        Self::create(&sdk, id, onmessage).await
    }

    pub async fn resume(sdk: &Sdk, id: String, onmessage: UnboundedSender<Message>) -> Session {
        Self::create(sdk, id, onmessage).await
    }

    async fn create(sdk: &Sdk, id: String, onmessage: UnboundedSender<Message>) -> Session {
        let mut url = sdk.options.base_url.clone();
        url.set_scheme("wss").unwrap();
        url.set_path("/v1/stream");
        url.set_query(Some(&format!("api_key={}&session_id={id}", &*sdk.options.api_key)));
        let (stream, _) =
            try_to("connect to Sec-Gemini web-socket", tokio_tungstenite::connect_async(url).await);
        let (mut sink, mut stream) = stream.split();
        drop(tokio::spawn(async move {
            while let Some(message) = stream.next().await {
                let message = match try_to("receive web-socket message", message) {
                    tungstenite::Message::Text(x) => x,
                    tungstenite::Message::Ping(_) => continue, // handled by tungstenite
                    x => fail!("Received unexpected web-socket message {x:?}"),
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
                try_to("send web-socket message", sink.send(message).await);
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
        try_to("send web-socket message", self.send.send(tungstenite::Message::text(message)));
    }
}
