import inspect
from typing import Callable, get_type_hints

JSON_TYPE = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def build_schema(func: Callable) -> dict:
    """함수 시그니처와 독스트링으로 도구 명세를 만든다."""
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    props, required = {}, []

    for name, param in sig.parameters.items():
        hint = hints.get(name, str)
        props[name] = {"type": JSON_TYPE.get(hint, "string")}

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            props[name]["default"] = param.default

    doc = (func.__doc__ or "").strip().split("\n")[0]

    return {
        "name": func.__name__,
        "description": doc,
        "parameters": {
            "type": "object",
            "properties": props,
            "required": required,
        },
    }

import functools

REGISTRY: dict[str, Callable] = {}

def tool(func: Callable) -> Callable:
    """이 함수를 도구로 등록한다."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.schema = build_schema(func)      # 2장에서 만든 것
    REGISTRY[func.__name__] = wrapper
    return wrapper
