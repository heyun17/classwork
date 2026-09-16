"""OpenAI 호출 (4장)

호출 템플릿은 ask() 하나입니다.
    지시문(instructions) + 질문(input) → 답 글자(output_text)
키는 .env 의 OPENAI_API_KEY 에서 자동으로 읽습니다. 코드에는 적지 않습니다.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (APIConnectionError, APIStatusError, AuthenticationError,
                    NotFoundError, OpenAI, PermissionDeniedError, RateLimitError)

load_dotenv(Path(__file__).parent / ".env")          # .env → 환경변수
MODEL = os.getenv("OPENAI_MODEL") or "gpt-5.6-luna"

# 역할 지시: AI가 어떤 사람처럼 답할지
SYSTEM_PROMPT = """너는 동네 피자 가게 '페퍼로니 연구소'의 매출 컨설턴트다.
사장님은 데이터 전문가가 아니다. 쉬운 한국어로, 오늘 바로 할 수 있는 행동을 제안한다."""

# 인사이트 질문 틀: {summary} 자리에 집계 요약이 들어간다
INSIGHT_TEMPLATE = """아래는 우리 가게의 매출 요약이다.

{summary}

위 숫자만 근거로 사장님께 조언 3가지를 해줘.
- 각 조언은 두 문장 이내
- 반드시 위의 숫자를 하나 이상 인용
- 번호(1. 2. 3.)로 시작하고, 마크다운 기호(**, #)는 쓰지 말 것"""


def has_key():
    return os.getenv("OPENAI_API_KEY", "").startswith("sk-")


def ask(question, system=SYSTEM_PROMPT):
    """AI에게 묻고 답 글자를 돌려준다 — 이 과정의 호출 템플릿"""
    client = OpenAI()                        # OPENAI_API_KEY 를 환경변수에서 읽음
    response = client.responses.create(
        model=MODEL,
        instructions=system,                 # 역할 지시
        input=question,                      # 질문
    )
    return response.output_text              # 답 글자만 꺼내기


def fail(message):
    return {"ok": False, "message": message}


def get_insight(summary_text):
    """대시보드 버튼용. 성공/실패를 {'ok':…, 'message':…} 로 돌려준다."""
    if not has_key():
        return fail(".env에 OPENAI_API_KEY를 넣고 서버를 다시 켜면 사용할 수 있어요.")
    try:
        answer = ask(INSIGHT_TEMPLATE.format(summary=summary_text))
        return {"ok": True, "message": answer}
    except AuthenticationError:          # 401
        return fail("API 키가 올바르지 않습니다(401). .env의 키를 확인하세요.")
    except PermissionDeniedError:        # 403
        return fail("이 키로는 요청이 허용되지 않습니다(403). 프로젝트 권한을 확인하세요.")
    except NotFoundError:                # 404
        return fail(f"모델 '{MODEL}'을 찾을 수 없습니다(404). OPENAI_MODEL을 확인하세요.")
    except RateLimitError:               # 429
        return fail("사용 한도 또는 크레딧이 부족합니다(429). Billing을 확인하세요.")
    except APIConnectionError:
        return fail("OpenAI 서버에 연결할 수 없습니다. 인터넷 연결을 확인하세요.")
    except APIStatusError as e:          # 그 밖의 API 오류
        return fail(f"AI 호출 오류({e.status_code}). 잠시 후 다시 시도하세요.")
