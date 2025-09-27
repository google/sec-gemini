import asyncio
import sys
from pathlib import Path
import rich
sys.path.insert(0, str(Path(__file__).parent.parent))

from sec_gemini import SecGemini, State
from sec_gemini.models.enums import MessageType, Role, MimeType, ResponseStatus
from sec_gemini.models.local_tool import LocalTool


import json
from typing import Callable, Literal, get_args

def create_function_from_spec(spec: dict) -> Callable:
    """
    Parses an OpenAI tool specification and dynamically creates a Python function.

    Args:
        spec: A dictionary representing the OpenAI tool JSON specification.

    Returns:
        A callable Python function object with proper signature, type hints,
        and docstring.
    """
    if spec.get("type") != "function" or "function" not in spec:
        raise ValueError("Invalid tool spec: 'type' must be 'function' and 'function' key must exist.")

    func_details = spec["function"]
    func_name = func_details["name"]
    func_description = func_details.get("description", "")

    parameters = func_details.get("parameters", {})
    props = parameters.get("properties", {})
    required_params = parameters.get("required", [])

    # A mapping from JSON schema types to Python types
    type_mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }

    # --- 1. Construct the function signature ---
    param_strings = []
    arg_docstrings = ["Args:"]

    # Use a local scope to define Literal types for enums
    local_scope = {"Literal": Literal}

    for name, details in props.items():
        param_type = details.get("type")

        # Handle enums by creating a Literal type
        if "enum" in details:
            enum_name = f"{name.capitalize()}Enum"
            enum_values = tuple(details["enum"])
            local_scope[enum_name] = Literal[enum_values]
            python_type = enum_name

            # Add enum choices to the parameter description
            enum_choices = f"Must be one of: {', '.join(map(repr, enum_values))}."
            details["description"] = f"{details.get('description', '')} {enum_choices}".strip()
        else:
            python_type = type_mapping.get(param_type, "Any")

        # Build the docstring for the argument
        arg_docstrings.append(f"    {name} ({python_type}): {details.get('description', '')}")

        # Determine if the parameter is required or optional (has a default)
        if name in required_params:
            param_strings.append(f"{name}: {python_type}")
        else:
            param_strings.append(f"{name}: {python_type} = None")

    signature = ", ".join(param_strings)

    # --- 2. Construct the full function code string ---
    full_docstring = f'"""{func_description}\n\n{"\n".join(arg_docstrings)}\n"""'

    # The function body can be a placeholder
    function_body = "    pass"

    code_string = f"def {func_name}({signature}):\n{full_docstring}\n{function_body}"

    print("--- Generated Python Code ---")
    print(code_string)
    print("---------------------------\n")

    # --- 3. Execute the code string to create the function ---
    # We pass the local_scope which contains our dynamically created Enum types
    exec_scope = {}
    exec(code_string, local_scope, exec_scope)

    return exec_scope[func_name]

# Define a simple tool
def get_weather(city: str) -> str:
    """Gets the weather for a given city."""
    city = city.lower().strip()
    if city == "new york" or city == "new york city" or city == "nyc":
        return "27C and sunny"
    elif city == "london":
        return "12C and cloudy"
    else:
        return "unknown"

async def main():
    # Simple command-line prompt: join all args, or use a default
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "what is the weather in new york?"

    sg = SecGemini(base_url="http://localhost:8000", base_websockets_url="ws://localhost:8000")
    print("SecGemini object instantiated correctly")

    # Create a session with the local tool
    session = sg.create_session(tools=[get_weather])
    print("Session created successfully with local tool")

    # Query the model with the prompt from the command line
    async for message in session.stream(prompt):
        if message.mime_type == MimeType.SERIALIZED_JSON:
            try:
                content = json.loads(message.content)
                rich.print(content)
            except json.JSONDecodeError:
                rich.print(f"[bold red]Failed to decode JSON:[/bold red] {message.content}")
        elif message.state.value == State.END.value:
            rich.print(f"[green]Done")
            return
        elif message.message_type.value == MessageType.INFO.value:
            rich.print(f"[blue]info: {message.get_content()}")
        else:
            rich.print(f"[white]{message.content}")

if __name__ == "__main__":
    asyncio.run(main())
