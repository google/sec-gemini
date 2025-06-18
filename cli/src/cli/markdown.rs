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
use std::error::Error;
use std::fmt::{Display, Write as _};
use std::fs::File;
use std::io::Read;
use std::path::{Path, PathBuf};

use clap::ValueHint;
use colored::Colorize;
use markdown::message::Message;
use markdown::{ParseOptions, mdast, to_mdast};

#[derive(clap::Args)]
pub struct Action {
    /// From where to read the markdown.
    #[arg(long, default_value = "-", value_hint = ValueHint::FilePath)]
    input: PathBuf,
}

impl Action {
    pub fn run(self) {
        let mut input: Box<dyn Read> = if self.input == Path::new("-") {
            Box::new(std::io::stdin())
        } else {
            let name = self.input.display();
            Box::new(try_to!("open file {name}", File::open(&self.input)))
        };
        let mut content = String::new();
        let _: usize = try_to!("read markdown", input.read_to_string(&mut content));
        let opts = ParseOptions::gfm();
        let md = try_to!("parse markdown", to_mdast(&content, &opts).map_err(MdError));
        let mut context = Context::default();
        let mut output = String::new();
        try_to!("render markdown", render_node(&mut context, &mut output, &md));
        println!("{output}");
    }
}

pub fn try_render_markdown(content: &str) -> Cow<'_, str> {
    match render_markdown(content) {
        Ok(x) => x.into(),
        Err(e) => {
            log::warn!("failed to render markdown: {e:?}");
            content.into()
        }
    }
}

fn render_markdown(content: &str) -> Result<String, RenderError> {
    let opts = ParseOptions::gfm();
    let md = to_mdast(content, &opts)?;
    let mut context = Context::default();
    let mut output = String::new();
    render_node(&mut context, &mut output, &md)?;
    Ok(output)
}

#[derive(Default)]
struct Context {
    list_depth: usize,
}

fn render_nodes(
    context: &mut Context, output: &mut String, nodes: &[mdast::Node],
) -> Result<(), RenderError> {
    for node in nodes {
        render_node(context, output, node)?;
    }
    Ok(())
}

fn render_node(
    context: &mut Context, output: &mut String, node: &mdast::Node,
) -> Result<(), RenderError> {
    match node {
        mdast::Node::Root(root) => {
            if let Some(node) = root.children.first() {
                render_node(context, output, node)?;
            }
            for nodes in root.children.windows(2) {
                match nodes[..] {
                    [mdast::Node::Definition(_), mdast::Node::Definition(_)] => (),
                    _ => ensure_newline(output),
                }
                render_node(context, output, &nodes[1])?;
            }
        }
        mdast::Node::Heading(heading) if heading.children.len() == 1 => {
            let mut header = "#".repeat(heading.depth as usize);
            header.push(' ');
            render_node(context, &mut header, &heading.children[0])?;
            writeln!(output, "{}", header.bold().purple())?;
        }
        mdast::Node::Text(text) => write!(output, "{}", text.value)?,
        mdast::Node::Paragraph(paragraph) => {
            render_nodes(context, output, &paragraph.children)?;
        }
        mdast::Node::LinkReference(link) => {
            let mut text = String::new();
            render_nodes(context, &mut text, &link.children)?;
            let ident = format!("[{}]", link.identifier);
            write!(output, "[{text}]{}", ident.blue())?;
        }
        mdast::Node::Code(code) => {
            writeln!(output, "{}", code.value.yellow())?;
        }
        mdast::Node::Definition(definition) => {
            let ident = format!("[{}]", definition.identifier);
            writeln!(output, "{}: {}", ident.bold().blue(), definition.url.blue())?;
        }
        mdast::Node::InlineCode(code) => {
            write!(output, "{}", code.value.yellow())?;
        }
        mdast::Node::Link(link) => {
            let link = match &link.children[..] {
                // We get nested Link for [foo](bar).
                [mdast::Node::Link(link)] => link,
                _ => link,
            };
            let mut text = String::new();
            render_nodes(context, &mut text, &link.children)?;
            if text == link.url {
                let url = format!("<{text}>");
                write!(output, "{}", url.blue())?;
            } else {
                let url = format!("({})", link.url);
                write!(output, "[{text}]{}", url.blue())?;
            }
        }
        mdast::Node::List(list) => {
            ensure_newline(output);
            let mut idx = list.start.unwrap_or(1) - 1;
            context.list_depth += 1;
            for node in &list.children {
                let ident = "    ".repeat(context.list_depth - 1);
                let bullet = if list.ordered {
                    idx += 1;
                    format!("{: }{idx}.", "")
                } else {
                    "*".to_string()
                };
                write!(output, "{ident}{} ", bullet.bold().purple())?;
                render_node(context, output, node)?;
                writeln!(output)?;
            }
            context.list_depth -= 1;
        }
        mdast::Node::ListItem(item) => render_nodes(context, output, &item.children)?,
        mdast::Node::Strong(strong) => {
            let mut text = String::new();
            render_nodes(context, &mut text, &strong.children)?;
            write!(output, "{}", text.bold().cyan())?;
        }
        mdast::Node::Emphasis(emphasis) => {
            let mut text = String::new();
            render_nodes(context, &mut text, &emphasis.children)?;
            write!(output, "{}", text.cyan())?;
        }
        x => return Err(RenderError::String(format!("unimplemented {x:?}"))),
    }
    Ok(())
}

fn ensure_newline(output: &mut String) {
    while !output.ends_with("\n\n") {
        output.push('\n');
    }
}

#[derive(Debug)]
enum RenderError {
    String(String),
    Format(std::fmt::Error),
    MdError(MdError),
}

impl Error for RenderError {}
impl Display for RenderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RenderError::String(x) => x.fmt(f),
            RenderError::Format(x) => x.fmt(f),
            RenderError::MdError(x) => x.fmt(f),
        }
    }
}

impl From<std::fmt::Error> for RenderError {
    fn from(value: std::fmt::Error) -> Self {
        RenderError::Format(value)
    }
}

impl From<Message> for RenderError {
    fn from(value: Message) -> Self {
        RenderError::MdError(MdError(value))
    }
}

#[derive(Debug)]
struct MdError(Message);

impl Error for MdError {}
impl Display for MdError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}
