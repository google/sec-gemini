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

use linefeed::{Interface, ReadResult};
use tokio::sync::mpsc::unbounded_channel;
use uuid::Uuid;

use crate::or_fail;
use crate::sdk::types::Message;
use crate::sdk::{Sdk, Session};

/// Opens an interactive session with Sec-Gemini in the terminal.
#[derive(clap::Parser)]
pub struct Action {}

impl Action {
    pub async fn run(self) {
        let (sdk, _) = Sdk::new().await;
        let (send, mut recv) = unbounded_channel::<Message>();
        let name = Uuid::new_v4().to_string();
        let session = Session::new(Arc::new(sdk), name, send).await;
        let interface = Arc::new(or_fail(Interface::new("sec-gemini")));
        or_fail(interface.set_prompt("\x1b[0m> \x1b[1m"));
        loop {
            let prompt = match or_fail(interface.read_line()) {
                ReadResult::Eof => break,
                ReadResult::Input(x) => x,
                ReadResult::Signal(x) => unreachable!("{x:?}"),
            };
            or_fail(write!(interface, "\x1b[0m"));
            if prompt.trim().is_empty() {
                continue;
            }
            crate::cli::query::execute(&prompt, &mut recv, &session).await;
            interface.add_history(prompt);
        }
    }
}
