from mcp.server.mcpserver import MCPServer

mcp = MCPServer("hint-test")


@mcp.tool()
def add_hint(a: int, b: int) -> int:
    """두 정수를 더한다."""
    return a + b


@mcp.tool()
def add_nohint(a, b):
    """두 값을 더한다."""
    return a + b


if __name__ == "__main__":
    mcp.run()