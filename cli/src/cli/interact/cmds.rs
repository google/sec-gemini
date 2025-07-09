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

use std::borrow::Cow;
use std::collections::HashMap;
use std::io::Read;
use std::pin::Pin;
use std::sync::Arc;
use std::time::Duration;

use colored::Colorize;
use indicatif::HumanDuration;
use tokio::runtime::Handle;

use crate::config::{self, DynConfig};
use crate::sdk::types::now;
use crate::sdk::{Sdk, Session};

pub struct Completer {
    sdk: Arc<Sdk>,
}

impl<Term: linefeed::Terminal> linefeed::Completer<Term> for Completer {
    fn complete(
        &self, word: &str, prompter: &linefeed::Prompter<'_, '_, Term>, start: usize, _end: usize,
    ) -> Option<Vec<linefeed::Completion>> {
        let buffer = prompter.buffer().strip_prefix("/")?;
        self.complete_command(&split_words(&buffer[.. start.saturating_sub(1)]), word)
    }

    fn word_start(
        &self, line: &str, end: usize, _prompter: &linefeed::Prompter<'_, '_, Term>,
    ) -> usize {
        quoted_word_start(&line[.. end])
    }

    fn quote<'a>(&self, word: &'a str) -> Cow<'a, str> {
        quote(word)
    }

    fn unquote<'a>(&self, word: &'a str) -> Cow<'a, str> {
        unquote(word)
    }
}

impl Completer {
    pub fn new(sdk: Arc<Sdk>) -> Self {
        Completer { sdk }
    }

    fn complete_command(
        &self, mut prefix: &[Cow<'_, str>], word: &str,
    ) -> Option<Vec<linefeed::Completion>> {
        let help = match prefix.first() {
            Some(x) if x == "help" => {
                prefix = &prefix[1 ..];
                true
            }
            _ => false,
        };
        let mut slash = !help;
        let mut commands = COMMANDS;
        for name in prefix {
            let command = commands.iter().find(|x| x.name == name)?;
            slash = false;
            match command.data {
                CommandData::Node { cmds } => commands = cmds,
                CommandData::Leaf { .. } if help => return None,
                CommandData::Leaf { args, .. } => return self.complete_argument(args, word),
            }
        }
        let prefix = if slash { "/" } else { "" };
        let word = word.strip_prefix(prefix).unwrap();
        let mut completions: Vec<_> = (commands.iter())
            .filter(|x| x.name.starts_with(word))
            .map(|x| linefeed::Completion::simple(format!("{prefix}{}", x.name)))
            .collect();
        if slash && "help".starts_with(word) {
            completions.push(linefeed::Completion::simple("/help".to_string()));
        }
        Some(completions)
    }

    fn complete_argument(
        &self, arguments: &'static [Argument], word: &str,
    ) -> Option<Vec<linefeed::Completion>> {
        let compl = |x: &Argument| linefeed::Completion {
            completion: format!("--{}", x.name),
            display: None,
            suffix: linefeed::Suffix::Some('='),
        };
        let Some(word) = word.strip_prefix("--") else {
            return Some(arguments.iter().map(compl).collect());
        };
        match word.split_once('=') {
            None => {
                Some(arguments.iter().filter(|x| x.name.starts_with(word)).map(compl).collect())
            }
            Some((name, word)) => {
                let argument = arguments.iter().find(|x| x.name == name)?;
                let options: Box<dyn Iterator<Item = Cow<'_, str>>> = match argument.data {
                    ArgumentData::Value => return None,
                    ArgumentData::Enum { opts } => Box::new(opts.iter().map(|&x| x.into())),
                    ArgumentData::Custom(compl) => {
                        Box::new(compl(self).into_iter().map(Into::into))
                    }
                };
                let compl = |x| linefeed::Completion::simple(format!("--{name}={x}"));
                Some(options.filter(|x| x.starts_with(word)).map(compl).collect())
            }
        }
    }
}

pub async fn execute_command(query: &str, mut input: CommandInput<'_>) {
    let full_query = split_words(query);
    let mut query = &full_query[..];
    let mut help = match query.first() {
        Some(x) if x == "help" => {
            query = &query[1 ..];
            Some(
                "Provides help about the available commands.\n
Examples:
  /help
  /help session
  /help session list",
            )
        }
        _ => None,
    };
    let partial_query = |f: &[_], q: &[_]| join_words(&f[.. f.len() - q.len()]);
    let options = |cmds: &[Command]| match cmds {
        [] => unreachable!(),
        [cmd] => cmd.name.to_string(),
        [first, cmds @ .., last] => {
            let mut options = format!("one of {}", first.name);
            for cmd in cmds {
                options.push_str(", ");
                options.push_str(cmd.name);
            }
            if !cmds.is_empty() {
                options.push(',');
            }
            options.push_str(" or ");
            options.push_str(last.name);
            options
        }
    };
    let mut commands = COMMANDS;
    let (exec, arguments) = loop {
        match query.split_first() {
            None if help.is_some() => {
                println!("{}", help.unwrap());
                println!("\nCommands:");
                for command in commands {
                    let mut cmd = "/".to_string();
                    for x in &full_query[1 ..] {
                        cmd.push_str(x);
                        cmd.push(' ');
                    }
                    let mut cmd = cmd.blue();
                    if full_query.len() == 1 {
                        cmd = cmd.bold();
                    }
                    println!("  {cmd}{}", command.name.bold().blue());
                }
                return;
            }
            None => {
                return user_error!(
                    "expected {} after {}",
                    options(commands),
                    partial_query(&full_query, query)
                );
            }
            Some((name, rest)) => {
                let Some(command) = commands.iter().find(|x| x.name == name) else {
                    let partial_query = partial_query(&full_query, query);
                    if partial_query.is_empty() {
                        return user_error!("unknown command {name}");
                    } else {
                        return user_error!("unknown subcommand {name} for {partial_query}");
                    }
                };
                if let Some(help) = &mut help {
                    *help = command.help;
                }
                query = rest;
                match command.data {
                    CommandData::Node { cmds } => commands = cmds,
                    CommandData::Leaf { exec, args } => break (exec, args),
                }
            }
        }
    };
    if let Some(help) = help {
        if !query.is_empty() {
            return user_error!(
                "unexpected continuation after {}",
                partial_query(&full_query, query)
            );
        }
        println!("{help}");
        if arguments.is_empty() {
            return;
        }
        println!("\nArguments:");
        for argument in arguments {
            let prefix = format!("--{}", argument.name);
            print!("  {}", prefix.bold().blue());
            if let ArgumentData::Enum { opts } = argument.data {
                print!(" {} ", "[options:".green());
                for (i, opt) in opts.iter().enumerate() {
                    if 0 < i {
                        print!("{} ", ",".green());
                    }
                    print!("{}", opt.bold().blue());
                }
                print!("{}", "]".green());
            }
            match argument.default {
                None => print!(" {}", "[required]".red()),
                Some(value) => print!(
                    " {} {}{}{}{}",
                    "[optional:".yellow(),
                    prefix.blue(),
                    "=".bold().blue(),
                    value.bold().blue(),
                    "]".yellow()
                ),
            }
            println!();
        }
        return;
    }
    let args = &mut input.args;
    while let Some((arg, rest)) = query.split_first() {
        query = rest;
        let Some(arg) = arg.strip_prefix("--") else {
            return user_error!(
                "expected argument (starting with --) after {}",
                partial_query(&full_query, query)
            );
        };
        let Some((key, val)) = arg.split_once('=') else {
            return user_error!("expected argument value (starting with =) after --{arg}");
        };
        if !arguments.iter().any(|x| x.name == key) {
            return user_error!("unknown argument --{key}");
        }
        if args.insert(key.to_string(), val.to_string()).is_some() {
            return user_error!("duplicate argument --{key}");
        }
    }
    for argument in arguments {
        if args.contains_key(argument.name) {
            continue;
        }
        match argument.default {
            Some(default) => {
                assert!(args.insert(argument.name.to_string(), default.to_string()).is_none())
            }
            None => return user_error!("argument --{} is required", argument.name),
        }
    }
    exec(input).await;
}

fn split_words(mut query: &str) -> Vec<Cow<'_, str>> {
    let mut words = Vec::new();
    while !query.is_empty() {
        let pos = quoted_word_start(query);
        if pos < query.len() {
            words.push(unquote(&query[pos ..]));
        }
        query = &query[.. pos.saturating_sub(1)];
    }
    words.reverse();
    words
}

fn join_words(mut words: &[Cow<'_, str>]) -> String {
    let mut query = String::new();
    while let Some((word, rest)) = words.split_first() {
        words = rest;
        if !query.is_empty() {
            query.push(' ');
        }
        query.push_str(&quote(word));
    }
    query
}

fn quote(mut word: &str) -> Cow<'_, str> {
    let Some(pos) = word.find(['\'', ' ']) else {
        return word.into();
    };
    let mut quoted = String::new();
    if word.starts_with("--") {
        if let Some(eq) = word.find('=') {
            if eq < pos {
                let (prefix, suffix) = word.split_at(eq + 1);
                quoted = prefix.to_string();
                word = suffix;
            }
        }
    }
    quoted.push('\'');
    for c in word.chars() {
        quoted.push(c);
        if c == '\'' {
            quoted.push('\'');
        }
    }
    quoted.push('\'');
    quoted.into()
}

#[test]
fn quote_ok() {
    assert_eq!(quote("hello"), "hello");
    assert_eq!(quote("hello world"), "'hello world'");
    assert_eq!(quote("can't"), "'can''t'");
    assert_eq!(quote("--foo=hello world"), "--foo='hello world'");
}

fn unquote(word: &str) -> Cow<'_, str> {
    if !word.contains('\'') {
        return word.into();
    }
    parse_quoted(word).map(|(_, _, c)| c).collect()
}

#[test]
fn unquote_ok() {
    assert_eq!(unquote("hello"), "hello");
    assert_eq!(unquote("hello world"), "hello world");
    assert_eq!(unquote("--foo='bar'"), "--foo=bar");
    assert_eq!(unquote("x'foo''bar'y'hello'z"), "xfoo'baryhelloz");
}

fn quoted_word_start(line: &str) -> usize {
    let mut last = 0;
    for (i, q, c) in parse_quoted(line) {
        if c == ' ' && !q {
            last = i + 1;
        }
    }
    last
}

#[test]
fn quoted_word_start_ok() {
    assert_eq!(quoted_word_start("hello"), 0);
    assert_eq!(quoted_word_start("hello world"), 6);
    assert_eq!(quoted_word_start("hello --foo='bar"), 6);
    assert_eq!(quoted_word_start("hello --foo='bar''bar' --next"), 23);
}

// Returns the sequence of quoted characters with their index and whether it is quoted.
fn parse_quoted(input: &str) -> impl Iterator<Item = (usize, bool, char)> {
    let mut within = -1;
    input.char_indices().filter_map(move |(i, c)| {
        if c == '\'' {
            within += 1;
            if within < 2 {
                return None;
            }
        }
        if 0 < within {
            within -= 2;
        }
        Some((i, within == 0, c))
    })
}

#[derive(Debug)]
struct Command {
    name: &'static str,
    help: &'static str,
    data: CommandData,
}

#[derive(Debug)]
enum CommandData {
    Node { cmds: &'static [Command] },
    Leaf { exec: CommandExec, args: &'static [Argument] },
}

pub struct CommandInput<'a> {
    pub this: &'a mut super::Options,
    pub sdk: &'a Arc<Sdk>,
    pub session: &'a mut Session,
    pub start: &'a str,
    pub clear: &'a str,
    pub args: HashMap<String, String>,
}
type CommandOutput<'a> = Pin<Box<dyn Future<Output = ()> + 'a>>;
type CommandExec = for<'a> fn(input: CommandInput<'a>) -> CommandOutput<'a>;

#[derive(Debug)]
struct Argument {
    name: &'static str,
    default: Option<&'static str>,
    data: ArgumentData,
}

#[derive(Debug)]
enum ArgumentData {
    Value,
    Enum { opts: &'static [&'static str] },
    Custom(fn(&Completer) -> Vec<String>),
}

fn exec_config(mut input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let name = &input.args["name"];
        if name.is_empty() {
            let width = config::list().map(|x| x.name().len()).max().unwrap();
            for config in config::list() {
                print_config(Some(width), config).await;
            }
            return;
        }
        let Some(config) = config::list().find(|x| x.name() == name) else {
            return user_error!("unknown --name={name}");
        };
        match input.args["action"].as_str() {
            "get" => (),
            "set" => {
                let value = input.args.remove("value").unwrap();
                if let Some(error) = config.validate(&value) {
                    return user_error!("invalid value: {error}");
                }
                DynConfig::set_user(config, value);
            }
            "unset" => config.unset(),
            "save" => {
                let (value, source) = config.get().await;
                match source {
                    config::Source::File => println!("Already saved."),
                    _ => config.write(value).await,
                }
            }
            "reset" => config.delete().await,
            x => user_error!("unknown --action={x}"),
        }
        print_config(None, config).await;
    })
}

async fn print_config(width: Option<usize>, config: &DynConfig) {
    let width = width.unwrap_or(config.name().len());
    print!("{:>width$}: ", config.name().purple());
    let (value, source) = config.get().await;
    match source {
        config::Source::File => return println!("{} (saved)", value.green()),
        _ => print!("{} (not saved, ", value.yellow()),
    }
    match config.get_file().await {
        None => println!("no saved value)"),
        Some(value) => println!("saved value is {})", value.cyan()),
    }
}

fn exec_multiline(input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let mut query = Vec::new();
        let mut stdin = std::io::stdin();
        loop {
            let mut buf = [0; 1024];
            let len = try_to!("read standard input", stdin.read(&mut buf));
            if len == 0 {
                break;
            }
            query.extend_from_slice(&buf[.. len]);
        }
        if !query.ends_with(b"\n") {
            println!();
        }
        let Ok(query) = String::from_utf8(query) else { return user_error!("query is not UTF-8") };
        println!("{}End of multiline query.{}", input.start, input.clear);
        input.this.execute(&query, input.session).await;
    })
}

fn exec_session_list(input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        match input.args["refresh"].as_str() {
            "true" => input.sdk.refresh_sessions().await,
            "false" => (),
            _ => return user_error!("argument --refresh expects true or false"),
        }
        let debug = input.args["debug"].as_str() == "true";
        for session in input.sdk.cached_sessions().await.iter() {
            if session.id == input.session.id() {
                print!("* {}", session.name.bold().cyan());
            } else {
                print!("- {}", session.name.cyan());
            }
            if debug {
                print!(" {}", session.id.yellow());
            }
            println!(
                " created {} ago ({} messages)",
                HumanDuration(Duration::from_secs(now() - session.create_time as u64)),
                session.num_messages
            );
        }
    })
}

fn exec_session_create(mut input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let name = input.args.remove("name").unwrap();
        *input.session = Session::new(input.sdk.clone(), name).await;
    })
}

fn exec_session_resume(input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let name = &input.args["name"];
        let id = match input.sdk.cached_sessions().await.iter().find(|x| x.name == *name) {
            Some(session) => session.id.clone(),
            None => return user_error!("no session named {name}"),
        };
        *input.session = Session::resume(input.sdk.clone(), id);
    })
}

fn exec_session_delete(input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let name = &input.args["name"];
        let mut sessions = input.sdk.cached_sessions().await;
        for (i, session) in sessions.iter().enumerate() {
            if &session.name == name {
                if session.id == input.session.id() {
                    return user_error!("cannot delete current session");
                }
                let _ = Session::delete(input.sdk, &session.id).await;
                let _ = sessions.remove(i);
                return;
            }
        }
        user_error!("no session named {name}");
    })
}

fn exec_shell(input: CommandInput<'_>) -> CommandOutput<'_> {
    Box::pin(async move {
        let command = format!("{}{}", super::shell::EXEC_SHELL_CMD, input.args["command"]);
        let response = input.this.shell.interpret_result(&command).await.unwrap();
        input.this.execute_updated(true, &response, input.session).await;
    })
}

fn compl_session_name(completer: &Completer) -> Vec<String> {
    Handle::current().block_on(async {
        completer.sdk.cached_sessions().await.iter().map(|x| x.name.clone()).collect()
    })
}

fn compl_config_name(_: &Completer) -> Vec<String> {
    config::list().map(|x| x.name().to_string()).collect()
}

macro_rules! make {
    (cmds $($cmd:tt)*) => (&[$(make!(cmd $cmd)),*]);
    (cmd [ $name:literal $help:literal $($cmd:tt)* ]) => {
        Command { name: $name, help: $help, data: CommandData::Node { cmds: make!(cmds $($cmd)*) } }
    };
    (cmd { $name:literal $help:literal $exec:ident$($arg:tt)* }) => {
        Command { name: $name, help: $help, data: CommandData::Leaf {
            exec: $exec, args: &[$(make!(arg $arg)),*] } }
    };
    (arg ( $name:literal $(= $default:literal)? : $($data:tt)* )) => {
        Argument { name: $name, default: make!(opt $($default)?), data: make!(data $($data)*) }
    };
    (data *) => (ArgumentData::Value);
    (data $($option:literal)+) => (ArgumentData::Enum { opts: &[$($option),+]});
    (data $compl:ident) => (ArgumentData::Custom($compl));
    (opt) => (None);
    (opt $val:literal) => (Some($val));
}

macro_rules! make_commands {
    ($($cmd:tt)*) => (make!(cmds $($cmd)*));
}

const COMMANDS: &[Command] = make_commands! {
    { "config" "Reads, writes, or deletes configuration values.\n
If --name is empty (the default), all configuration values are printed.\n
The --action argument controls the operation (ignored if --name is empty):
  - get: prints the current and config file value
  - set: updates the current value (for the current execution)
  - unset: resets the current value to the config file (if any)
  - save: saves the current value to the config file
  - reset: deletes the config file\n
The --value argument is only used by write operations."
       exec_config
       ( "name" = "" : compl_config_name )
       ( "action" = "get" : "get" "set" "unset" "save" "reset" )
       ( "value" = "" : * ) }
    { "multiline" "Reads a multi-line query.\n
The usual way to end the query is Ctrl-D (twice on a non-empty line)."
      exec_multiline }
    [ "session" "Provides operations on sessions."
       { "list" "Lists the user sessions."
          exec_session_list
          ( "refresh" = "false" : "true" "false" )
          ( "debug" = "false" : "true" "false" ) }
       { "create" "Creates a new session.\n
If the --name argument is an empty string (the default), a name is generated."
          exec_session_create ( "name" = "" : * ) }
       { "resume" "Resumes an existing session."
          exec_session_resume ( "name" : compl_session_name ) }
       { "delete" "Deletes an existing session.\n
The current session cannot be deleted."
          exec_session_delete ( "name" : compl_session_name ) } ]
    { "shell" "Executes a shell command as if Sec-Gemini requested it."
      exec_shell ( "command" : * ) }
};
