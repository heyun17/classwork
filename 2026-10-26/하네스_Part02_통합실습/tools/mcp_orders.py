"""선택 실습: MCP Python SDK가 설치된 환경에서만 동작한다.
Codex 등록 시 이 파일의 절대경로를 사용한다. 서버 본문은 stdout에 로그를 출력하지 않는다.
"""
from mcp.server.fastmcp import FastMCP
from order_lookup import lookup_order

mcp = FastMCP("orders-readonly")

@mcp.tool()
def get_order(order_id: str) -> dict:
    """주문 ID로 원본 데이터를 조회한다. 읽기 전용이며 데이터 수정 불가."""
    return lookup_order(order_id)

if __name__ == "__main__":
    mcp.run(transport="stdio")
