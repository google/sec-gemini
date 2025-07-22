import asyncio
import sys
from functools import wraps
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent.parent))


from sec_gemini import SecGemini


def sync(f):
    """Decorator that wraps coroutine with asyncio.run."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.command()
@click.argument(
    "jsonl_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=Path),
)
@click.option("--enable-logging", is_flag=True)
@sync
async def main(jsonl_path: Path, enable_logging: bool) -> None:
    sg = SecGemini()
    print("SecGemini object instantiated correctly")

    session = sg.create_session(enable_logging=enable_logging)
    print("Session created successfully")

    session.upload_and_attach_logs(jsonl_path)

    print(f"Logs table: {session.logs_table}")
    print("OK")


if __name__ == "__main__":
    main()
