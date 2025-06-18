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

use crate::StrError;
use crate::util::{read_file, remove_file};

static CONFIG_DIR: LazyLock<PathBuf> = LazyLock::new(|| {
    let dirs =
        try_to!("find Sec-Gemini config directory", ProjectDirs::from("", "Google", "Sec-Gemini"));
    dirs.config_dir().to_path_buf()
});

macro_rules! make {
    ($name:ident: $type:ty = $fallback:expr) => {
        pub static $name: Config<$type> = Config::new(DynConfig {
            name: unsafe {
                str::from_utf8_unchecked(&make_name::<{ stringify!($name).len() }>(stringify!(
                    $name
                )))
            },
            fallback: $fallback,
            value: Mutex::new(None),
            validate: no_validation,
        });
    };
}

make!(API_KEY: String = Fallback::Prompt("Sec-Gemini API key"));
make!(AUTO_EXEC: bool = Fallback::Default("false"));
make!(AUTO_SEND: bool = Fallback::Default("true"));
make!(BASE_URL: Url = Fallback::Default("https://api.secgemini.google"));
make!(ENABLE_SHELL: AutoBool = Fallback::Default("auto"));
make!(SHOW_THINKING: bool = Fallback::Default("false"));

#[derive(Clone, Copy, ValueEnum)]
pub enum Name {
    ApiKey,
    AutoExec,
    AutoSend,
    EnableShell,
    ShowThinking,
}

impl Name {
    pub fn config(self) -> &'static DynConfig {
        match self {
            Name::ApiKey => &API_KEY.config,
            Name::AutoExec => &AUTO_EXEC.config,
            Name::AutoSend => &AUTO_SEND.config,
            Name::EnableShell => &ENABLE_SHELL.config,
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

#[derive(Clone, Copy, ValueEnum)]
pub enum AutoBool {
    Auto,
    False,
    True,
}

impl Display for AutoBool {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.to_possible_value().unwrap().get_name())
    }
}

impl FromStr for AutoBool {
    type Err = StrError;
    fn from_str(input: &str) -> Result<Self, Self::Err> {
        <AutoBool as ValueEnum>::from_str(input, true).map_err(StrError)
    }
}

impl AutoBool {
    pub fn guess(self, def: impl Fn() -> bool) -> bool {
        match self {
            AutoBool::Auto => def(),
            AutoBool::False => false,
            AutoBool::True => true,
        }
    }
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
    /// From some user input (flag, env, or command).
    User,
    /// From the config file.
    File,
    /// From the fallback (prompt).
    Term,
    /// From the fallback (default).
    None,
}

impl Display for Source {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Source::User => write!(f, "user input"),
            Source::File => write!(f, "config file"),
            Source::Term => write!(f, "terminal"),
            Source::None => write!(f, "default"),
        }
    }
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
        let Fallback::Prompt(prompt) = self.fallback else { unreachable!() };
        let value = self.get_term(prompt);
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
            None => match self.fallback {
                Fallback::Prompt(x) => (self.get_term(x), Source::Term),
                Fallback::Default(x) => (x.to_string(), Source::None),
            },
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
    fn get_term(&self, prompt: &str) -> String {
        let name = self.name;
        let instr = self.instr();
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
        let mut env = "SEC_GEMINI_".to_string();
        for c in self.0.name.chars() {
            env.push(match c {
                '-' => '_',
                _ => c.to_ascii_uppercase(),
            });
        }
        write!(f, "Set the --{} flag or the {env} environment variable.", self.0.name)
    }
}

fn no_validation(_: &str) -> Option<String> {
    None
}

const fn make_name<const N: usize>(x: &str) -> [u8; N] {
    let mut y = [0; N];
    let x = x.as_bytes();
    let mut i = 0;
    while i < x.len() {
        y[i] = match x[i] {
            b'_' => b'-',
            b @ b'A' ..= b'Z' => b - b'A' + b'a',
            b @ b'0' ..= b'9' => b,
            _ => panic!(),
        };
        i += 1;
    }
    y
}
