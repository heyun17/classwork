from test.registry import tools


@tools
def add(a: int, b: int) -> int:
    return a + b