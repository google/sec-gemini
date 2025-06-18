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

use std::convert::Infallible;
use std::error::Error;
use std::fmt::Display;

use colored::Colorize;

macro_rules! _fmt {
    ($fmt:literal) => {
        std::format_args!($fmt)
    };
    (($($fmt:tt)*)) => {
        std::format_args!($($fmt)*)
    };
}

macro_rules! _opt {
    () => {
        None
    };
    ($val:expr) => {
        Some($val)
    };
}

macro_rules! fail {
    ($fmt:tt $(, $source:expr $(, $suggestion:expr)?)?) => {
        crate::fail(_fmt!($fmt), _opt!($($source)?), _opt!($($($suggestion)?)?))
    };
}

macro_rules! try_to {
    ($fmt:tt , $value:expr $(, $($suggestion:expr)?)?) => {
        crate::try_to(_fmt!($fmt), $value, _opt!($($($suggestion)?)?))
    };
}

macro_rules! user_error {
    ($($fmt:tt)*) => {{
        print!("{}: ", "Error".red());
        println!($($fmt)*);
    }};
}

mod cli;
mod config;
mod sdk;
mod util;

#[tokio::main]
async fn main() {
    env_logger::init();
    <cli::Action as clap::Parser>::parse().run().await
}

#[derive(Debug)]
pub struct StrError(String);

impl Error for StrError {}
impl Display for StrError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

fn fail(
    message: impl Display, mut source: Option<&dyn Error>, suggestion: Option<&dyn Display>,
) -> ! {
    println!("{}: {message}", "Error".bold().red());
    while let Some(error) = source {
        println!("{}: {error}", "cause".red());
        source = error.source();
    }
    if let Some(suggestion) = suggestion {
        println!("\n{suggestion}");
    }
    std::process::exit(1);
}

fn or_fail<T, E: Error>(x: Result<T, E>) -> T {
    x.unwrap_or_else(|e| fail(e.to_string(), e.source(), None))
}

fn try_to<T>(action: impl Display, value: impl ToResult<T>, suggestion: Option<&dyn Display>) -> T {
    value.to_result().unwrap_or_else(|error| {
        fail(format!("failed to {action}"), error.as_ref().map(|x| x as &dyn Error), suggestion)
    })
}

trait ToResult<T> {
    type Error: Error;
    fn to_result(self) -> Result<T, Option<Self::Error>>;
}

impl<T> ToResult<T> for Option<T> {
    type Error = Infallible;
    fn to_result(self) -> Result<T, Option<Self::Error>> {
        self.ok_or(None)
    }
}

impl<T, E: Error> ToResult<T> for Result<T, E> {
    type Error = E;
    fn to_result(self) -> Result<T, Option<Self::Error>> {
        self.map_err(Some)
    }
}
