import argparse
import asyncio
import json
import sys
from pathlib import Path

import rich
from rich.markdown import Markdown

sys.path.insert(0, str(Path(__file__).parent.parent))

from sec_gemini import SecGemini, State
from sec_gemini.models.enums import MessageType, MimeType


def list_dir(path: str = ".") -> list[str]:
    """List files in a directory."""
    p = Path(path)
    return [str(f) for f in p.iterdir()]


def read_file(file_path: str) -> str:
    """Read the content of a file."""
    p = Path(file_path)
    if not p.is_file():
        return f"Error: {file_path} is not a valid file."
    return p.read_text()


def grep_file(file_path: str, search_term: str) -> list[str]:
    """Search for a term in a file and return matching lines."""
    p = Path(file_path)
    if not p.is_file():
        return [f"Error: {file_path} is not a valid file."]
    with p.open() as f:
        return [line.strip() for line in f if search_term in line]


def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    p = Path(file_path)
    try:
        p.write_text(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file: {e}"


def append_file(file_path: str, content: str) -> str:
    """Append content to a file."""
    p = Path(file_path)
    try:
        with p.open("a") as f:
            f.write(content)
        return f"Successfully appended to {file_path}"
    except Exception as e:
        return f"Error appending to file: {e}"


def delete_file(file_path: str) -> str:
    """Delete a file."""
    p = Path(file_path)
    if not p.is_file():
        return f"Error: {file_path} is not a valid file."
    try:
        p.unlink()
        return f"Successfully deleted {file_path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def list_processes() -> list[str]:
    """List the current running processes."""
    import subprocess

    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        return result.stdout.splitlines()
    except Exception as e:
        return [f"Error listing processes: {e}"]


def get_ip() -> str:
    """Get the IP address of the machine."""
    import platform
    import subprocess

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, check=True
            )
        else:
            result = subprocess.run(
                ["ifconfig"], capture_output=True, text=True, check=True
            )
        return result.stdout
    except Exception as e:
        return f"Error getting IP address: {e}"


def get_route() -> str:
    """Get the routing table of the machine."""
    import platform
    import subprocess

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["route", "print"], capture_output=True, text=True, check=True
            )
        else:
            result = subprocess.run(
                ["netstat", "-rn"], capture_output=True, text=True, check=True
            )
        return result.stdout
    except Exception as e:
        return f"Error getting routing table: {e}"


def get_os_info() -> str:
    """Get the OS information of the machine."""
    import platform

    return f"System: {platform.system()}, Release: {platform.release()}, Version: {platform.version()}"


def sha256_file(file_path: str) -> str:
    """Calculate the SHA256 hash of a file."""
    import hashlib

    p = Path(file_path)
    if not p.is_file():
        return f"Error: {file_path} is not a valid file."
    try:
        hasher = hashlib.sha256()
        with p.open("rb") as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception as e:
        return f"Error calculating SHA256: {e}"


def tail_file(file_path: str, n_lines: int = 10) -> list[str]:
    """Return the last N lines of a file."""
    p = Path(file_path)
    if not p.is_file():
        return [f"Error: {file_path} is not a valid file."]
    try:
        with p.open() as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-n_lines:]]
    except Exception as e:
        return [f"Error reading file: {e}"]


def head_file(file_path: str, n_lines: int = 10) -> list[str]:
    """Return the first N lines of a file."""
    p = Path(file_path)
    if not p.is_file():
        return [f"Error: {file_path} is not a valid file."]
    try:
        with p.open() as f:
            lines = [next(f) for _ in range(n_lines)]
        return [line.strip() for line in lines]
    except StopIteration:
        # If the file has fewer than n_lines, we'll get a StopIteration
        with p.open() as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        return [f"Error reading file: {e}"]


def regex_search_file(file_path: str, pattern: str) -> list[str]:
    """Search for a regex pattern in a file and return matching lines."""
    import re

    p = Path(file_path)
    if not p.is_file():
        return [f"Error: {file_path} is not a valid file."]
    try:
        matches = []
        with p.open() as f:
            for line in f:
                if re.search(pattern, line):
                    matches.append(line.strip())
        return matches
    except Exception as e:
        return [f"Error searching file: {e}"]


def get_disk_size(path: str = ".") -> str:
    """Get the total and free disk space for a given path."""
    import shutil

    try:
        total, used, free = shutil.disk_usage(path)
        return f"Total: {total // (2**30)} GiB, Used: {used // (2**30)} GiB, Free: {free // (2**30)} GiB"
    except Exception as e:
        return f"Error getting disk size: {e}"


toolist = [
    list_dir,
    read_file,
    grep_file,
    write_file,
    append_file,
    delete_file,
    list_processes,
    get_ip,
    get_route,
    get_os_info,
    sha256_file,
    tail_file,
    head_file,
    regex_search_file,
    get_disk_size,
]


async def main():
    parser = argparse.ArgumentParser(
        description="A script that uses SecGemini to interact with local tools."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="which files are in my current dir ?",
        help="The prompt to send to the model.",
    )
    parser.add_argument(
        "-l",
        "--list-tools",
        action="store_true",
        help="List available tools and their descriptions.",
    )
    args = parser.parse_args()

    if args.list_tools:
        print("Available tools:")
        for tool in toolist:
            print(f"  - {tool.__name__}: {tool.__doc__}")
        return

    prompt = args.prompt
    sg = SecGemini()
    print("SecGemini object instantiated correctly")

    # Create a session with the local tool
    session = sg.create_session(tools=toolist)
    print("Session created successfully with local tool")

    # Query the model with the prompt from the command line
    async for message in session.stream(prompt):
        if message.mime_type == MimeType.SERIALIZED_JSON:
            try:
                content = json.loads(message.content)
                if "tool_name" in content:
                    tool_name = content["tool_name"]
                    tool_args = content.get("args")
                    if not tool_args:
                        tool_args = content.get("tool_args", {})

                    argstr = ", ".join(f"{k}={v!r}" for k, v in tool_args.items())

                    rich.print(f"[green][bold]{tool_name}[/bold]\n{argstr}[/green]")
                else:
                    rich.print(content)
            except json.JSONDecodeError:
                rich.print(
                    f"[bold red]Failed to decode JSON:[/bold red] {message.content}"
                )
        elif message.state.value == State.END.value:
            rich.print("[green]Done")
            return
        elif message.message_type.value == MessageType.INFO.value:
            rich.print(f"[blue]info: {message.get_content()}")
        else:
            md = Markdown(message.content)
            rich.print("[white]", md)


if __name__ == "__main__":
    asyncio.run(main())
