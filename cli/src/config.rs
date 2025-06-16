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

use std::error::Error;
use std::fmt::Display;
use std::marker::PhantomData;
use std::ops::Deref;
use std::path::PathBuf;
use std::str::FromStr;
use std::sync::{LazyLock, Mutex, MutexGuard};

use clap::ValueEnum;
use dialoguer::Input;
use directories::ProjectDirs;
use url::Url;

use crate::util::{read_file, remove_file};

static CONFIG_DIR: LazyLock<PathBuf> = LazyLock::new(|| {
    let dirs =
        try_to!("find Sec-Gemini config directory", ProjectDirs::from("", "Google", "Sec-Gemini"));
    dirs.config_dir().to_path_buf()
});

pub static API_KEY: Config<String> = Config::new(DynConfig {
    name: "api-key",
    fallback: Fallback::Prompt("Sec-Gemini API key"),
    flag: "--api-key",
    env: "SEC_GEMINI_API_KEY",
    value: Mutex::new(None),
    validate: no_validation,
});

pub static BASE_URL: Config<Url> = Config::new(DynConfig {
    name: "base-url",
    fallback: Fallback::Default("https://api.secgemini.google"),
    flag: "--base-url",
    env: "SEC_GEMINI_BASE_URL",
    value: Mutex::new(None),
    validate: no_validation,
});

pub static SHOW_THINKING: Config<bool> = Config::new(DynConfig {
    name: "show-thinking",
    fallback: Fallback::Default("false"),
    flag: "--show-thinking",
    env: "SEC_GEMINI_SHOW_THINKING",
    value: Mutex::new(None),
    validate: no_validation,
});

#[derive(Clone, Copy, ValueEnum)]
pub enum Name {
    ApiKey,
    ShowThinking,
}

impl Name {
    pub fn config(self) -> &'static DynConfig {
        match self {
            Name::ApiKey => &API_KEY.config,
            Name::ShowThinking => &SHOW_THINKING.config,
        }
    }
}

#[test]
fn name_config_ok() {
    for name in Name::value_variants() {
        let config = name.config();
        assert_eq!(name.to_possible_value().unwrap().get_name(), config.name());
    }
}

pub fn list() -> impl Iterator<Item = &'static DynConfig> {
    Name::value_variants().iter().map(|x| x.config())
}

/// A typed configurable global value.
pub struct Config<T> {
    config: DynConfig,
    type_: PhantomData<T>,
}

/// A untyped configurable global value.
pub struct DynConfig {
    /// The name of the config file.
    name: &'static str,
    /// The fallback when the config file does not exist.
    fallback: Fallback,
    /// The name of the flag.
    flag: &'static str,
    /// The name of the environment variable.
    env: &'static str,
    /// The current value.
    value: Mutex<Value>,
    /// Validates a value.
    validate: fn(&str) -> Option<String>,
}

enum Fallback {
    Prompt(&'static str),
    Default(&'static str),
}

type Value = Option<(String, Source)>;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Source {
    /// The value was set by reading the config file.
    File,
    /// The value was set by asking the user interactively in the terminal.
    Term,
    /// The value was set by the user interactively.
    User,
}

impl<T> Deref for Config<T> {
    type Target = DynConfig;

    fn deref(&self) -> &Self::Target {
        &self.config
    }
}

impl<T: Clone + FromStr + Display> Config<T>
where <T as FromStr>::Err: Error
{
    const fn new(mut config: DynConfig) -> Self {
        fn validate<T: FromStr>(input: &str) -> Option<String>
        where <T as FromStr>::Err: Display {
            match input.parse::<T>() {
                Ok(_) => None,
                Err(e) => Some(format!("{e}")),
            }
        }
        config.validate = validate::<T>;
        Config { config, type_: PhantomData }
    }

    pub async fn get(&self) -> (T, Source) {
        let name = self.config.name;
        let (value, source) = self.config.get().await;
        (try_to!("parse {name} config", value.parse()), source)
    }

    pub fn set_user(&self, value: T) {
        self.config.set_user(format!("{value}"));
    }
}

impl DynConfig {
    pub fn name(&self) -> &'static str {
        self.name
    }

    pub fn set_user(&self, value: String) {
        *self.value() = Some((value, Source::User));
    }

    pub fn set_term(&self) {
        let value = self.get_term();
        *self.value() = Some((value, Source::Term));
    }

    pub fn unset(&self) {
        *self.value() = None;
    }

    /// Returns the current value (reading from file and terminal if needed).
    pub async fn get(&self) -> (String, Source) {
        if let Some(ref x) = *self.value() {
            return x.clone();
        }
        let (value, source) = match self.get_file().await {
            None => (self.get_term(), Source::Term),
            Some(value) => (value, Source::File),
        };
        let result = value.clone();
        *self.value() = Some((value, source));
        (result, source)
    }

    /// Reads from the config file.
    pub async fn get_file(&self) -> Option<String> {
        let name = self.name;
        let path = CONFIG_DIR.join(name);
        let content = try_to!("read {name} config file", read_file(&path).await)?;
        match String::from_utf8(content) {
            Ok(value) => Some(value),
            Err(_) => {
                log::warn!("{name} config file is not UTF-8 (deleting it)");
                try_to!("delete {name} config file", remove_file(&path).await);
                None
            }
        }
    }

    /// Reads from the terminal.
    pub fn get_term(&self) -> String {
        let name = self.name;
        let instr = self.instr();
        let prompt = match self.fallback {
            Fallback::Prompt(x) => x,
            Fallback::Default(x) => return x.to_string(),
        };
        try_to!("read {name} config from terminal", console::user_attended().then_some(()), &instr);
        try_to!(
            "read {name} config from terminal",
            Input::new().with_prompt(format!("Enter your {prompt}")).interact_text(),
            &instr
        )
    }

    /// Persists the config if read from terminal (does nothing otherwise).
    pub async fn persist(&self) {
        let (value, source) = self.get().await;
        if source != Source::Term {
            return;
        }
        self.write(value).await;
    }

    /// Writes a value to the config file (and use that value).
    pub async fn write(&self, value: String) {
        let name = self.name;
        let config_dir = &*CONFIG_DIR;
        let path = config_dir.join(name);
        log::info!("Writing {}", path.display());
        try_to!("create Sec-Gemini config directory", tokio::fs::create_dir_all(config_dir).await);
        try_to!("write {name} config file", tokio::fs::write(path, value.as_bytes()).await);
        *self.value() = Some((value, Source::File));
    }

    /// Deletes the config file (and unset the value).
    pub async fn delete(&self) {
        let name = self.name;
        let path = CONFIG_DIR.join(name);
        try_to!("delete {name} config file", remove_file(path).await);
        *self.value() = None;
    }

    pub fn validate(&self, value: &str) -> Option<String> {
        (self.validate)(value)
    }

    fn value(&self) -> MutexGuard<'_, Value> {
        let name = self.name;
        try_to!("lock {name} config mutex", self.value.lock())
    }

    fn instr(&self) -> ConfigInstr<'_> {
        ConfigInstr(self)
    }
}

struct ConfigInstr<'a>(&'a DynConfig);

impl<'a> std::fmt::Display for ConfigInstr<'a> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Set the {} flag or the {} environment variable.", self.0.flag, self.0.env)
    }
}

fn no_validation(_: &str) -> Option<String> {
    None
}
