from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import monitoring.hourly as hourly
import monitoring.live_store as live_store


def test_live_log_and_periodic_snapshot(tmp_path, monkeypatch):
    db_path = tmp_path / "monitor.db"
    monkeypatch.setattr(live_store, "DB_PATH", db_path)
    monkeypatch.setattr(hourly, "DB_PATH", db_path)
    monkeypatch.setattr(hourly, "notify", lambda subject, message: ("record_only", "test"))

    now = datetime(2026, 9, 17, 10, 0, 0)

    # 정상 FAQ 로그 1건
    live_store.log_chat_usage(
        employee_id="E0001",
        department="인사",
        category="급여",
        question_text="월급 문의",
        question_type="text",
        route="TEXT_FAQ",
        resolved=1,
        created_at="2026-09-17 09:59:20",
    )

    # 오류/토큰 과다/재시도 로그를 넣어 이상치 탐지 확인
    for i in range(6):
        live_store.log_chat_usage(
            employee_id="E9999",
            department="전산",
            category="장애",
            question_text="테스트",
            question_type="text",
            route="LLM",
            api_required=1,
            resolved=0,
            input_tokens=7000,
            output_tokens=1000,
            api_call_count=2,
            retry_count=1,
            status_code=504 if i == 0 else 200,
            error_type="timeout" if i == 0 else None,
            created_at=f"2026-09-17 09:59:{30+i:02d}",
        )

    assert live_store.pending_live_count() == 7

    result = hourly.run_hourly_monitor(now=now, lookback_seconds=60)
    assert result["sessions"] == 7
    assert result["alerts"] >= 1
    assert result["retries"] == 6

    snapshots = live_store.read_hourly_snapshots()
    assert len(snapshots) == 1
    assert int(snapshots.iloc[0]["sessions"]) == 7

    employee = live_store.read_employee_snapshots(window_end=result["window_end"])
    assert "E9999" in set(employee["employee_id"])

    alerts = live_store.read_alert_history()
    assert not alerts.empty
    assert live_store.pending_live_count() == 0
