import inspect
from typing import Any, Callable, Literal, Optional, Union, get_args, get_origin

from mcp.server.fastmcp.tools import Tool

from sec_gemini.models.local_tool import LocalTool


def function_to_localtool(tool: Callable) -> LocalTool:
    """
    Convert a Python function into a LocalTool object."""

    mcp_tool = Tool.from_function(tool)
    local_tool = LocalTool.from_dict(mcp_tool.model_dump())
    return local_tool


def localtool_to_function(local_tool: LocalTool) -> Callable:
    """
    Convert a LocalTool passed by one of the client into a Dummy Python function.
    """
    tool_spec = local_tool.to_dict()
    fn_name = tool_spec["name"]
    fn_description = tool_spec.get("description", "")

    fn_parameters = tool_spec.get("parameters", {})
    fn_props = fn_parameters.get("properties", {})
    fn_required_params = fn_parameters.get("required", [])

    type_mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }

    param_strings = []
    arg_docstrings = ["Args:"]
    local_scope = {"Literal": Literal, "Optional": Optional, "Union": Union, "Any": Any}

    for name, details in fn_props.items():
        param_type = details.get("type")

        if "enum" in details:
            enum_name = f"{name.capitalize()}Enum"
            enum_values = tuple(details["enum"])
            local_scope[enum_name] = Literal[enum_values]
            python_type = enum_name
            enum_choices = f"Must be one of: {', '.join(map(repr, enum_values))}."
            details["description"] = (
                f"{details.get('description', '')} {enum_choices}".strip()
            )
        else:
            python_type = type_mapping.get(param_type, "Any")

        arg_docstrings.append(
            f"    {name} ({python_type}): {details.get('description', '')}"
        )

        if name in fn_required_params:
            param_strings.append(f"{name}: {python_type}")
        else:
            default_value = details.get("default")
            if default_value is not None:
                param_strings.append(f"{name}: {python_type} = {repr(default_value)}")
            else:
                param_strings.append(f"{name}: Optional[{python_type}] = None")

    signature_str = ", ".join(param_strings)
    args = "\n\t".join(arg_docstrings)
    desc = f"\t{fn_description}\n\n\t{args}\n"
    full_docstring = f'\t"""{desc}\t"""'

    function_body = "\treturn locals()"

    code_string = f"def {fn_name}({signature_str}):\n{full_docstring}\n{function_body}"

    exec_scope = {}
    exec(code_string, local_scope, exec_scope)
    return exec_scope[fn_name]


def are_functions_equivalent(func1: Callable, func2: Callable, *args, **kwargs) -> bool:
    """
    Checks if two functions produce the same output for the same input.
    """
    try:
        output1 = func1(*args, **kwargs)
        output2 = func2(*args, **kwargs)
        return output1 == output2
    except Exception as e:
        print(f"Error during function execution: {e}")
        return False


def generate_test_args(func: Callable) -> dict:
    """Generates a dictionary of test arguments for a given function."""
    test_args = {}
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        # We only generate arguments for parameters that don't have a default value.
        if param.default is not inspect.Parameter.empty:
            continue

        param_name = param.name
        param_type = param.annotation

        origin = get_origin(param_type)
        args = get_args(param_type)

        if origin is Literal:
            # Use the first value from the Literal enum
            if args:
                test_args[param_name] = args[0]
        elif origin is Union:
            # Find the first non-None type in the Union and generate a value for it
            real_type = next((t for t in args if t is not type(None)), None)
            if real_type is str:
                test_args[param_name] = "test_string_for_union"
            elif real_type is int:
                test_args[param_name] = 42
            else:
                # Fallback for other types in Union
                test_args[param_name] = "fallback_union_value"
        elif param_type is str:
            test_args[param_name] = "/generated/path"
        elif param_type is int:
            test_args[param_name] = 99
        elif param_type is float:
            test_args[param_name] = 3.14
        elif param_type is bool:
            test_args[param_name] = True
        elif param_type is list:
            test_args[param_name] = ["generated", "list"]
        elif param_type is dict:
            test_args[param_name] = {"gen_key": "gen_value"}
        else:
            # Fallback for any other required parameter type
            test_args[param_name] = "generic_fallback"

    return test_args


def test_run_all_tool_tests() -> None:
    # --- Test Functions ---
    def problematic_tool(path: str = None):
        """A tool with a str annotation but a None default."""
        return {"path": path}

    def list_directory(path: str = "."):
        """Lists the contents of a directory."""
        return {"path": path}

    def fixed_tool_optional(path: Optional[str] = None):
        """A tool with an Optional[str] annotation and a None default."""
        return {"path": path}

    def fixed_tool_union(path: Union[str, None] = None):
        """A tool with a Union[str, None] annotation and a None default."""
        return {"path": path}

    def tool_with_enum(location: Literal["north", "south", "east", "west"] = "north"):
        """A tool with an enum parameter."""
        return {"location": location}

    def tool_with_multiple_args(name: str, age: int, is_student: bool = False):
        """A tool with multiple arguments."""
        return {"name": name, "age": age, "is_student": is_student}

    def tool_with_list(items: list):
        """A tool with a list argument."""
        return {"items": items}

    def tool_with_dict(data: dict):
        """A tool with a dict argument."""
        return {"data": data}

    def tool_with_no_args():
        """A tool with no arguments."""
        return {}

    def tool_with_multiline_docstring(x: int, y: int):
        """
        This is a multiline docstring.

        It has multiple lines.
        """
        return {"x": x, "y": y}

    def tool_with_complex_enum(
        action: Literal["CREATE", "UPDATE", "DELETE"] = "CREATE",
    ):
        """A tool with a more complex enum."""
        return {"action": action}

    def tool_with_union(value: Union[int, str]):
        """A tool with a union type."""
        return {"value": value}

    def tool_with_false_default(is_active: bool = False):
        """A tool with a boolean parameter with a False default."""
        return {"is_active": is_active}

    def tool_with_float(price: float):
        """A tool with a float parameter."""
        return {"price": price}

    def tool_with_optional_int(value: Optional[int] = None):
        """A tool with an optional int parameter."""
        return {"value": value}

    test_functions = [
        problematic_tool,
        list_directory,
        fixed_tool_optional,
        fixed_tool_union,
        tool_with_enum,
        tool_with_multiple_args,
        tool_with_list,
        tool_with_dict,
        tool_with_no_args,
        tool_with_multiline_docstring,
        tool_with_complex_enum,
        tool_with_union,
        tool_with_false_default,
        tool_with_float,
        tool_with_optional_int,
    ]

    for func in test_functions:
        print(f"--- Testing: {func.__name__} ---")
        print(f"Original signature: {inspect.signature(func)}")

        # 1. Convert to LocalTool
        local_tool = function_to_localtool(func)
        print("Generated LocalTool JSON:")
        print(local_tool.to_json())

        # 2. Convert back to function
        recreated_function = localtool_to_function(local_tool)
        print(f"Recreated signature: {inspect.signature(recreated_function)}")

        # 3. Equivalence Check
        test_args = generate_test_args(func)

        print(f"Executing with args: {test_args}")
        equivalent = are_functions_equivalent(func, recreated_function, **test_args)
        print(f"Functions are equivalent: {equivalent}")
        print("-" * (len(func.__name__) + 14))
        print()


if __name__ == "__main__":
    test_run_all_tool_tests()
