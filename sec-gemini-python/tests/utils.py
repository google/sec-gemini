import functools
import os
import string

import pytest


def require_env_variable(env_var_name):
    """
    A pytest decorator that skips a test if the specified environment variable
    is not set.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            env_value = os.getenv(env_var_name, "").strip()

            if env_value != "":
                return func(*args, **kwargs)
            else:
                pytest.skip(
                    f"Skipping test '{func.__name__}': Environment variable '{env_var_name}' is not set with a valid value."
                )
                return

        return wrapper

    return decorator


def async_require_env_variable(env_var_name):
    """
    A pytest decorator that skips a test if the specified environment variable
    is not set.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            env_value = os.getenv(env_var_name, "").strip()

            if env_value != "":
                return await func(*args, **kwargs)
            else:
                pytest.skip(
                    f"Skipping test '{func.__name__}': Environment variable '{env_var_name}' is not set with a valid value."
                )
                return

        return wrapper

    return decorator


def parse_secgemini_response(content: str) -> str:
    """Parse SecGemini response.

    When interacting with the prod backend, this is trivial. But in dev, the
    output is somewhat a table. This function parses out far-right cell in the
    last row, which should be the "result response".
    """

    if content.rstrip().endswith("|"):
        return (
            content.rstrip(string.whitespace + "|").rsplit("|", 1)[-1].strip().lower()
        )
    else:
        return content.lower()
