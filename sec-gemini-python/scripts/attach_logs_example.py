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
@click.option(
    "--fmap",
    "custom_fields_mapping_entries",
    multiple=True,
    type=str,
    help="Define a custom field map in 'DEST_FIELD:SOURCE_FIELD' format. Can be used multiple times.",
)
@sync
async def main(
    jsonl_path: Path,
    enable_logging: bool,
    custom_fields_mapping_entries: tuple[str, ...],
) -> None:
    custom_fields_mapping = {}
    for item in custom_fields_mapping_entries:
        try:
            key, value = item.split(":", 1)
            custom_fields_mapping[key] = value
        except ValueError:
            raise click.UsageError(
                f"Invalid mapping format for '{item}'. "
                "Expected format is 'DEST_FIELD:SOURCE_FIELD'."
            )
    if len(custom_fields_mapping) > 0:
        print(f"Parsed custom fields mapping: {custom_fields_mapping}")

    sg = SecGemini()
    print("SecGemini object instantiated correctly")

    session = sg.create_session(enable_logging=enable_logging)
    print("Session created successfully")

    session.upload_and_attach_logs(
        jsonl_path, custom_fields_mapping=custom_fields_mapping
    )

    print(f"Logs table: {session.logs_table}")
    print("OK")


if __name__ == "__main__":
    main()
