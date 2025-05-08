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
use std::time::Duration;

use indicatif::ProgressBar;
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender, unbounded_channel};

use crate::cli::FLAGS;
use crate::sdk::types::{Message, MessageType, PublicSessionOutput, Role};
use crate::sdk::{Sdk, Session};

/// Sends a single query to Sec-Gemini and prints the result.
#[derive(clap::Parser)]
pub struct Action {
    /// The prompt of the query.
    ///
    /// You can use multiple arguments, in which case they will be separated by spaces. The
    /// following invocations are equivalent (with common shell escaping):
    ///
    ///     sec-gemini query 'what is a CVE'
    ///     sec-gemini query what is a CVE
    ///     sec-gemini query   'what is'     a\ CVE
    #[arg(verbatim_doc_comment)]
    prompt: Vec<String>,
}

impl Action {
    pub async fn run(self) {
        let prompt = self.prompt.join(" ");
        if prompt.len() < 5 {
            fail!("The prompt is too short.");
        }
        let (sdk, sessions) = Sdk::new().await;
        let (send, mut recv) = unbounded_channel::<Message>();
        let session = get_session(Arc::new(sdk), sessions, send).await;
        execute(&prompt, &mut recv, &session).await
    }
}

pub async fn execute(prompt: &str, recv: &mut UnboundedReceiver<Message>, session: &Session) {
    let progress = ProgressBar::new_spinner();
    progress.set_message("Sending request");
    progress.enable_steady_tick(Duration::from_millis(200));
    session.send(prompt);
    progress.set_message("Waiting response");
    while let Some(message) = recv.recv().await {
        let content = message.content.unwrap_or_default().unwrap_or_default();
        match message.message_type {
            MessageType::Result => {
                if message.role == Some(Role::System) {
                    if FLAGS.execution_flow {
                        print!("{content}");
                    }
                    break;
                }
                progress.finish_and_clear();
                println!("{}", content.trim_end());
            }
            MessageType::Info => progress.set_message(content),
            MessageType::Error => fail!("{content}"),
            _ => (),
        }
    }
}

async fn get_session(
    sdk: Arc<Sdk>, sessions: Vec<PublicSessionOutput>, send: UnboundedSender<Message>,
) -> Session {
    const SESSION_NAME: &str = "sec-gemini query";
    let mut best = None;
    for session in sessions {
        if session.name != SESSION_NAME {
            continue;
        }
        let Some(id) = session.id else { continue };
        let Some(create_time) = session.create_time else { continue };
        match best {
            Some((best_time, _)) if create_time < best_time => (),
            _ => best = Some((create_time, id)),
        }
    }
    if let Some((_, id)) = best {
        log::info!("Resuming existing CLI session.");
        Session::resume(id, send).await
    } else {
        log::info!("Creating new CLI session.");
        Session::new(sdk, SESSION_NAME.to_string(), send).await
    }
}
