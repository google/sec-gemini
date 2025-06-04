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
use std::fmt::{Arguments, Display};

use colored::Colorize;

macro_rules! fail {
    ($fmt:literal $(, $($args:expr)*)? $(; $source:expr)? $(=> $suggestion:expr)?) => {
        crate::fail(
            std::format_args!($fmt $(, $($args)*)?),
            fail!(opt $($source)?),
            fail!(opt $($suggestion)?),
        )
    };
    (opt) => (None);
    (opt $val:expr) => (Some($val));
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
struct StrError<'a>(&'a str);

impl Error for StrError<'_> {}
impl Display for StrError<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

fn fail(
    message: Arguments<'_>, mut source: Option<&dyn Error>, suggestion: Option<&dyn Display>,
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

fn fail_str(message: &str, source: Option<&dyn Error>, suggestion: Option<&dyn Display>) -> ! {
    fail(format_args!("{message}"), source, suggestion)
}

fn or_fail<T, E: Error>(x: Result<T, E>) -> T {
    match x {
        Ok(x) => x,
        Err(e) => match e.source() {
            Some(s) => fail!("{e}"; s),
            None => fail!("{e}"),
        },
    }
}

fn try_to<T, E: Error>(f: &str, x: Result<T, E>) -> T {
    match x {
        Ok(x) => x,
        Err(e) => fail!("failed to {f}"; &e),
    }
}

fn try_to_opt<T>(f: &str, x: Option<T>) -> T {
    match x {
        Some(x) => x,
        None => fail!("failed to {f}"),
    }
}
