from test.registry import tools


@tools
def hello(name: str) -> str:
    return f"안녕 {name}"