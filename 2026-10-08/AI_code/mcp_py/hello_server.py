from datetime import datetime

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("hello")


@mcp.tool()
def say_hello(name: str) -> str:
    """이름을 받아 인사말을 돌려준다."""
    return f"안녕하세요, {name}님!"


@mcp.tool()
def now() -> str:
    """현재 시각을 'YYYY-MM-DD HH:MM:SS' 형식으로 돌려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    mcp.run()