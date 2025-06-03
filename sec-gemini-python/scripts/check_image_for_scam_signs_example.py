import base64
import os
import sys
from pathlib import Path

import click
import dotenv
import magika
from openai import OpenAI

dotenv.load_dotenv()


@click.command()
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
def main(file_path: Path) -> None:
    api_key = os.getenv("SEC_GEMINI_API_KEY", "").strip()
    if api_key == "":
        print(
            "ERROR: this example requires a valid api key in the SEC_GEMINI_API_KEY env variable"
        )
        sys.exit(1)

    base_url = os.getenv("SEC_GEMINI_API_HTTP_URL", "https://api.secgemini.google")

    print(f'Connecting to "{base_url}"')

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        max_retries=1,
    )

    b64encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    mime_type = magika.Magika().identify_path(file_path).output.mime_type
    if not mime_type.startswith("image/"):
        print(f"ERROR: files with mime type {mime_type} are not supported")
        sys.exit(1)

    response = client.chat.completions.create(
        model="sec-gemini-1.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Is this file a scam or depicting a scam?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64encoded}"},
                    },
                ],
            }
        ],
    )

    print(f"Raw response {response}")


if __name__ == "__main__":
    main()
