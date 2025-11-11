"""Demonstration of Sec-Gemini's logs reasoning agent with local search."""

import argparse
import asyncio

import rich

import sec_gemini as sg
import sec_gemini.logs_reasoning.sqlite_backend.sqlite as sq
from sec_gemini import MessageType


async def main():
  """Main function."""
  parser = argparse.ArgumentParser(
    description="Sec-Gemini's logs analysis agent."
  )
  parser.add_argument(
    "--sg_agent",
    type=str,
    default="logs_analysis_agent-1.1",
    help="Name of the Sec-Gemini agent to use.",
  )
  parser.add_argument(
    "--prompt",
    required=True,
    type=str,
    default=(
      "Perform a forensics investigation on the provided logs. Determine if"
      " the host has been compromized, and if so, reconstruct the complete"
      " attacker timeline starting from initial access. You can only search"
      " in the following logs and nothing else during this investigation."
    ),
    help="The prompt to send to the model.",
  )
  parser.add_argument(
    "--sqlite",
    required=True,
    type=str,
    help="Path to the local sqlite logs database.",
  )
  parser.add_argument(
    "--n_records_to_sample",
    type=int,
    default=2,
    help=(
      "Number of randomly sampled log records to show per log type for"
      " explaining the contents of the logs."
    ),
  )
  args = parser.parse_args()
  print("Initializing local logstore...", end=" ")
  logstore = sq.SQLiteStore(args.sqlite, args.n_records_to_sample)
  session_tools = logstore.make_tools()
  print("OK")
  print("Creating Sec-Gemini session...", end=" ")
  sec_gem = sg.SecGemini()
  session = sec_gem.create_session(tools=session_tools, model=args.sg_agent)
  print("OK")

  async for message in session.stream(args.prompt):
    msg_type = message.message_type.value
    content = f"**[{msg_type.capitalize()}]** "
    if msg_type in [MessageType.THINKING.value, MessageType.RESULT.value]:
      if message.title:
        content += f"**{message.title.strip()}**\n\n"
      else:
        content += "\n"
      if message.content:
        content += message.content
    else:
      if message.title:
        content += f" {message.title}"
      if message.content and message.content != message.title:
        content += f" {message.content}"
    md = rich.markdown.Markdown(content)
    rich.print(md)


if __name__ == "__main__":
  asyncio.run(main())
