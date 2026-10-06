import test

from test.registry import call_tool


print(call_tool("add", {"a": 10, "b": 20}))