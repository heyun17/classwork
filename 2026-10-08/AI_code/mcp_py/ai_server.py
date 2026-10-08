import os
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
from pydantic import Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

mcp = MCPServer("ai-tools")


def get_client() -> tuple[AsyncOpenAI, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key:
        raise ToolError("OPENAI_API_KEY가 없습니다. .env를 확인하세요.")
    if not model:
        raise ToolError("OPENAI_MODEL이 없습니다. .env에 모델 ID를 넣으세요.")
    return AsyncOpenAI(api_key=api_key, timeout=30), model


@mcp.tool()
async def summarize(
    text: Annotated[str, Field(description="요약할 원문", min_length=1)],
    max_sentences: Annotated[int, Field(description="요약 문장 수", ge=1, le=10)] = 3,
) -> str:
    """긴 글을 한국어로 요약한다."""
    client, model = get_client()
    try:
        res = await client.responses.create(
            model=model,
            instructions=f"한국어로 {max_sentences}문장 이내로 요약하라.",
            input=text,
        )
    except OpenAIError as e:
        raise ToolError(f"OpenAI 호출 실패: {type(e).__name__}") from e
    return res.output_text


if __name__ == "__main__":
    mcp.run()