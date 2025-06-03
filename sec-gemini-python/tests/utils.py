import functools
import os

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
