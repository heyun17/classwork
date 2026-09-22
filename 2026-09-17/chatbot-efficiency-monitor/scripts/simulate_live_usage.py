"""개발용 실시간 로그 생성기.

실제 LLM API를 연결하지 않은 상태에서도 1분 집계/이상치/알림 흐름을 확인하기 위한
테스트 전용 스크립트다. --anomaly 옵션을 주면 토큰 과다/재시도/API 오류 예시를 넣는다.
"""
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monitoring.live_store import log_chat_usage


def create_normal_logs(count: int = 10) -> None:
    departments = ["전산", "인사", "총무", "재무", "법무"]
    for i in range(count):
        use_api = i % 2 == 0
        input_tokens = random.randint(700, 1800) if use_api else 0
        output_tokens = random.randint(150, 500) if use_api else 0
        log_chat_usage(
            employee_id=f"E{1000 + i:04d}",
            department=random.choice(departments),
            category="개발 시뮬레이션",
            question_text="개발용 정상 사용 시뮬레이션",
            question_type="simulated",
            route="LLM" if use_api else "TEXT_FAQ",
            api_required=int(use_api),
            resolved=1,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            api_call_count=int(use_api),
            status_code=200 if use_api else 0,
            api_cost_krw=(input_tokens + output_tokens) * 0.004,
        )


def create_anomaly_logs() -> None:
    # 한 직원의 세션당 토큰 과다 + 재시도 + API 오류를 의도적으로 만든다.
    for i in range(6):
        log_chat_usage(
            employee_id="E9999",
            department="전산",
            category="개발 이상치 시뮬레이션",
            question_text="개발용 이상치 테스트",
            question_type="simulated",
            route="LLM",
            api_required=1,
            resolved=0 if i < 3 else 1,
            input_tokens=6500 + i * 500,
            output_tokens=1200,
            api_call_count=2 if i < 3 else 1,
            retry_count=1 if i < 5 else 0,
            status_code=504 if i == 0 else 200,
            error_type="timeout" if i == 0 else None,
            api_cost_krw=35.0 + i,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--anomaly", action="store_true", help="이상치 로그도 추가")
    parser.add_argument("--count", type=int, default=10, help="정상 로그 수")
    args = parser.parse_args()

    create_normal_logs(args.count)
    if args.anomaly:
        create_anomaly_logs()
    print("개발용 실시간 로그 저장 완료")
