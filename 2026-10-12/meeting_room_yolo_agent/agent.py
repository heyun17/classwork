import json
from pathlib import Path

from openai import OpenAI

from config import MAX_AGENT_STEPS, OPENAI_MODEL
from tools import TOOLS, analyze_all_rooms, recent_history


client = OpenAI()

SYSTEM_PROMPT = (
    Path(__file__)
    .with_name("AGENTS.md")
    .read_text(encoding="utf-8")
)


def call_tool(name: str, arguments: dict) -> dict:
    """에이전트가 호출할 수 있는 Tool을 Allowlist 방식으로 제한한다."""
    if name == "analyze_all_rooms":
        return analyze_all_rooms()

    if name == "recent_history":
        return recent_history(**arguments)

    return {
        "ok": False,
        "error": f"허용되지 않은 Tool: {name}",
    }


def run_agent(user_request: str) -> str:
    """Responses API + Function Calling으로 Agent Loop를 실행한다."""
    input_messages = [
        {
            "role": "user",
            "content": user_request,
        }
    ]

    # Guardrail: Agent가 Tool 호출을 무한 반복하지 못하도록 제한한다.
    for _ in range(MAX_AGENT_STEPS):
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            tools=TOOLS,
            tool_choice="auto",
            input=input_messages,
        )

        # OpenAI 공식 Function Calling 패턴:
        # 모델 출력(function_call 포함)을 다음 입력 목록에 보존한다.
        input_messages += response.output

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # Tool 요청이 없으면 최종 자연어 답변이다.
        if not tool_calls:
            return response.output_text

        for tool_call in tool_calls:
            try:
                arguments = json.loads(
                    tool_call.arguments or "{}"
                )
                result = call_tool(
                    tool_call.name,
                    arguments,
                )
            except Exception as error:
                result = {
                    "ok": False,
                    "error": str(error),
                }

            input_messages.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                }
            )

    return (
        "⚠️ 에이전트가 최대 실행 횟수를 초과하여 "
        "작업을 중단했습니다."
    )
