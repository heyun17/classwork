import asyncio

from mcp import Client

from ai_server import mcp

TEXT = """MCP는 LLM 애플리케이션과 외부 도구를 연결하는 표준 프로토콜이다.
Server는 Tool, Resource, Prompt를 제공하고 Client는 JSON-RPC로 요청한다.
Codex는 config.toml에 등록된 Server를 실행해 도구를 사용한다."""


async def main() -> None:
    async with Client(mcp) as client:
        r = await client.call_tool("summarize", {"text": TEXT, "max_sentences": 1})
        print(r.is_error, r.content[0].text)


asyncio.run(main())