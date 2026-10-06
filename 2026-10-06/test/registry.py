import inspect
from typing import get_type_hints

from pydantic import ConfigDict, ValidationError, create_model


REGISTRY = {}


def build_input_model(func):
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    fields = {}

    for name, param in sig.parameters.items():
        field_type = hints.get(name, str)

        if param.default is inspect.Parameter.empty:
            default = ...
        else:
            default = param.default

        fields[name] = (field_type, default)

    return create_model(
        f"{func.__name__}Input",
        __config__=ConfigDict(strict=True),
        **fields,
    )


def tools(func):
    input_model = build_input_model(func)

    REGISTRY[func.__name__] = {
        "function": func,
        "input_model": input_model,
        "schema": input_model.model_json_schema(),
    }

    return func


def call_tool(name: str, arguments: dict):
    tool = REGISTRY[name]

    validated = tool["input_model"].model_validate(arguments)

    return tool["function"](**validated.model_dump())