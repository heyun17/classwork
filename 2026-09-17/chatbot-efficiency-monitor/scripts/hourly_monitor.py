from pathlib import Path
import argparse
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monitoring.config import MONITOR_INTERVAL_SECONDS
from monitoring.hourly import run_hourly_monitor


def print_result(result: dict) -> None:
    print(
        f"[{result['window_start']} ~ {result['window_end']}] "
        f"sessions={result['sessions']} alerts={result['alerts']} "
        f"tokens={result['input_tokens'] + result['output_tokens']} "
        f"api_calls={result['api_calls']} retries={result['retries']} "
        f"errors={result['errors']} api_cost={result['api_cost_krw']:.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="챗봇 주기별 집계/이상치 알림")
    parser.add_argument("--once", action="store_true", help="한 번만 실행하고 종료")
    args = parser.parse_args()

    print(f"모니터링 시작: {MONITOR_INTERVAL_SECONDS}초마다 집계합니다.")
    print("주기 변경은 monitoring/config.py의 MONITOR_INTERVAL_SECONDS 한 줄만 수정하세요.")

    while True:
        result = run_hourly_monitor(lookback_seconds=MONITOR_INTERVAL_SECONDS)
        print_result(result)
        if args.once:
            break
        time.sleep(MONITOR_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
