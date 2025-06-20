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

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;
use uuid::Uuid;

macro_rules! api {
    (pub enum $Name:ident { $($field:ident,)* }) => {
        #[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum $Name { $($field,)* #[serde(other)] Other }
    };
    (pub struct $Name:ident $Builder:ident {
        $($(#[$attr:meta])*
          pub $field:ident $($name:literal)?: $type:ty $(= $default:expr)?,)*
    }) => {
        #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
        pub struct $Name {
            $($(#[$attr])* pub $field: $type,)*
        }
        pub struct $Builder {
            $(pub $field: api!(builder_field_type $type $(= $default)?),)*
        }
        impl $Builder {
            api!(builder_new [] [] $({ $field: $type $(= $default)? })*);
            #[allow(dead_code)]
            pub fn build(self) -> $Name {
                $Name {
                    $($field: api!(builder_field_unwrap self $field: $type $(= $default)?),)*
                }
            }
            $(api!(builder_method $field: $type $(= $default)?);)*
        }
    };
    (builder_field_type $type:ty) => { $type };
    (builder_field_type $type:ty = $default:expr) => { Option<$type> };
    (builder_new [$($params:tt)*] [$($body:tt)*]) => {
        #[allow(dead_code)]
        pub fn new($($params)*) -> Self { Self { $($body)* } }
    };
    (builder_new [$($params:tt)*] [$($body:tt)*] { $field:ident: $type:ty } $($rest:tt)*) => {
        api!(builder_new [$($params)* $field: $type,] [$($body)* $field,] $($rest)*);
    };
    (builder_new $param:tt [$($body:tt)*] { $field:ident: $type:ty = $d:expr } $($rest:tt)*) => {
        api!(builder_new $param [$($body)* $field: None,] $($rest)*);
    };
    (builder_field_unwrap $this:ident $field:ident: $type:ty) => { $this.$field };
    (builder_field_unwrap $this:ident $field:ident: $type:ty = $default:expr) => {
        $this.$field.unwrap_or_else(|| $default)
    };
    (builder_method $field:ident: $type:ty) => {};
    (builder_method $field:ident: $type:ty = $default:expr) => {
        #[allow(dead_code)]
        #[allow(clippy::wrong_self_convention)]
        pub fn $field(mut self, value: $type) -> Self {
            self.$field = Some(value);
            self
        }
    };
}

pub const ROOT_ID: &str = "3713";

api! {
    pub struct Message MessageBuilder {
        pub id: String = uuid4_short(),
        pub parent_id: String = ROOT_ID.to_string(),
        pub turn: String = uuid4_short(),
        pub group: String = uuid4(),
        pub actor: String = "user".to_string(),
        pub role: Role = Role::User,
        pub timestamp: u64 = now(),
        pub message_type: MessageType,
        pub message_sub_type: Option<String> = None,
        pub state: State = State::Start,
        pub content: Option<String> = None,
        pub mime_type: Option<MimeType> = None,
        pub status_code: u16 = 200,
        pub status_message: String = "OK".to_string(),
        pub usage: Option<Usage> = None,
    }
}

api! {
    pub enum MessageType {
        Result,
        Source,
        Debug,
        Info,
        Error,
        Thinking,
        Update,
        Delete,
        ConfirmationRequest,
        ConfirmationResponse,
        Query,
        ResponseComplete,
    }
}

pub type MimeType = String; // we don't try to list them at this point

api! {
    pub struct ModelInfo ModelInfoBuilder {
        pub model_name: String,
        pub version: String,
        pub use_experimental: bool = false,
        pub model_string: String,
        pub description: Option<String> = Some("".to_string()),
        pub toolsets: Vec<OptionalToolSet> = Vec::new(),
    }
}

api! {
    pub struct OpResult OpResultBuilder {
        pub ok: bool,
        pub status_code: u16,
        pub status_message: String = String::new(),
        pub data: Option<BTreeMap<String, Value>> = None,
        pub mime_type: Option<MimeType> = Some("text/plain".to_string()),
        pub latency: Option<f64> = Some(0.0),
    }
}

type OptionalToolSet = Value; // we don't use them

api! {
    pub struct PublicSession PublicSessionBuilder {
        pub id: String = uuid4(),
        pub user_id: String,
        pub org_id: String,
        pub model: ModelInfo,
        pub ttl: u64,
        pub language: String = "en".to_string(),
        pub turns: u64 = 0,
        pub name: String,
        pub description: String,
        pub create_time: f64 = now() as f64,
        pub update_time: f64 = now() as f64,
        pub num_messages: u64 = 0,
        pub messages: Vec<Message> = Vec::new(),
        pub usage: Usage = UsageBuilder::new().build(),
        pub can_log: bool = true,
        pub state: State = State::Start,
        pub files: Vec<PublicSessionFile> = Vec::new(),
    }
}

type PublicSessionFile = Value; // we don't use them

api! {
    pub struct PublicUser PublicUserBuilder {
        pub id: String,
        pub org_id: String,
        pub r#type: UserType = UserType::User,
        pub never_log: bool = false,
        pub can_disable_logging: bool = false,
        pub key_expire_time: u64 = 0,
        pub tpm: u64 = 0,
        pub rpm: u64 = 0,
        pub allow_experimental: bool = false,
        pub vendors: Vec<PublicUserVendor> = Vec::new(),
    }
}

type PublicUserVendor = Value; // we don't use them

api! {
    pub enum Role {
        User,
        Agent,
        System,
    }
}

api! {
    pub enum State {
        Start,
        Query,
        RunningAgent,
        AgentDone,
        Coding,
        CodeResult,
        CallingTool,
        ToolResult,
        Generating,
        Answering,
        Thinking,
        Planning,
        Reviewing,
        Understanding,
        Retriving,
        Grounding,
    }
}

api! {
    pub struct Usage UsageBuilder {
        pub prompt_tokens: u64 = 0,
        pub generated_tokens: u64 = 0,
        pub total_tokens: u64 = 0,
        #[serde(default)]
        pub cached_total_tokens: u64 = 0,
        #[serde(default)]
        pub thoughts_total_tokens: u64 = 0,
        #[serde(default)]
        pub tool_use_prompt_token_count: u64 = 0,
    }
}

api! {
    pub struct UserInfo UserInfoBuilder {
        pub user: PublicUser,
        pub sessions: Vec<PublicSession> = Vec::new(),
        pub available_models: Vec<ModelInfo> = Vec::new(),
    }
}

api! {
    pub enum UserType {
        Ui,
        User,
        Admin,
        System,
        Service,
    }
}

pub fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn uuid4() -> String {
    Uuid::new_v4().as_simple().to_string()
}

fn uuid4_short() -> String {
    format!("{:.12x}", Uuid::new_v4().as_simple())
}
