from __future__ import annotations

from datetime import datetime, timedelta
import sqlite3

from monitoring.anomaly_rules import detect_hourly_anomalies
from monitoring.live_store import DB_PATH, ensure_live_tables, read_live_logs
from monitoring.notifier import notify


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def _get_state(key: str) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM monitor_state WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _set_state(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO monitor_state(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def run_hourly_monitor(now: datetime | None = None, lookback_seconds: int = 3600) -> dict:
    """미반영 실시간 로그를 주기 집계하고 이상치 알림을 기록/전송한다.

    함수 이름은 hourly지만 개발 모드에서는 lookback_seconds=60으로 실행할 수 있다.
    실제 운영에서는 3600(1시간)으로 사용한다.
    """
    ensure_live_tables()
    end_dt = now or datetime.now()
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    last = _get_state("last_hourly_check")
    if last:
        start = last
    else:
        start = (end_dt - timedelta(seconds=int(lookback_seconds))).strftime("%Y-%m-%d %H:%M:%S")

    df = read_live_logs(start=start, end=end)
    alerts = detect_hourly_anomalies(df)

    sessions = len(df)
    resolved = int(df["resolved"].sum()) if sessions else 0
    escalated = int(df["escalated"].sum()) if sessions else 0
    input_tokens = int(df["input_tokens"].sum()) if sessions else 0
    output_tokens = int(df["output_tokens"].sum()) if sessions else 0
    api_calls = int(df["api_call_count"].sum()) if sessions else 0
    retries = int(df["retry_count"].sum()) if sessions else 0
    errors = int((~df["status_code"].fillna(0).astype(int).isin([0, 200])).sum()) if sessions else 0
    non_work = int(df["route"].eq("NON_WORK").sum()) if sessions else 0
    api_cost = float(df["api_cost_krw"].sum()) if sessions else 0.0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO hourly_snapshots(
                window_start, window_end, sessions, resolved, escalated,
                input_tokens, output_tokens, api_calls, retries, errors,
                non_work_sessions, api_cost_krw, anomaly_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                start,
                end,
                sessions,
                resolved,
                escalated,
                input_tokens,
                output_tokens,
                api_calls,
                retries,
                errors,
                non_work,
                api_cost,
                len(alerts),
                created_at,
            ),
        )

        # 최신 구간의 직원별 토큰/오류 원인을 대시보드에서 볼 수 있게 별도 집계한다.
        if sessions:
            emp = df.copy()
            emp["total_tokens"] = emp["input_tokens"].fillna(0) + emp["output_tokens"].fillna(0)
            emp["is_error"] = ~emp["status_code"].fillna(0).astype(int).isin([0, 200])
            grouped = emp.groupby(["employee_id", "department"], as_index=False).agg(
                sessions=("session_id", "count"),
                resolved=("resolved", "sum"),
                api_calls=("api_call_count", "sum"),
                retries=("retry_count", "sum"),
                errors=("is_error", "sum"),
                input_tokens=("input_tokens", "sum"),
                output_tokens=("output_tokens", "sum"),
                total_tokens=("total_tokens", "sum"),
                api_cost_krw=("api_cost_krw", "sum"),
            )
            conn.executemany(
                """
                INSERT INTO hourly_employee_snapshots(
                    window_start, window_end, employee_id, department,
                    sessions, resolved, api_calls, retries, errors,
                    input_tokens, output_tokens, total_tokens, api_cost_krw, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        start,
                        end,
                        row.employee_id,
                        row.department,
                        int(row.sessions),
                        int(row.resolved),
                        int(row.api_calls),
                        int(row.retries),
                        int(row.errors),
                        int(row.input_tokens),
                        int(row.output_tokens),
                        int(row.total_tokens),
                        float(row.api_cost_krw),
                        created_at,
                    )
                    for row in grouped.itertuples(index=False)
                ],
            )

        for alert in alerts:
            subject = f"[챗봇 모니터링][{alert['severity'].upper()}] {alert['alert_type']}"
            message = (
                f"집계 구간: {start} ~ {end}\n"
                f"{alert['message']}\n\n"
                "관리자 대시보드에서 최근 토큰, 재시도, 오류 내역을 확인하세요."
            )
            sent_via, send_status = notify(subject, message)
            conn.execute(
                """
                INSERT INTO alert_history(
                    created_at, window_start, window_end, severity, alert_type,
                    employee_id, message, sent_via, send_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    start,
                    end,
                    alert["severity"],
                    alert["alert_type"],
                    alert.get("employee_id"),
                    alert["message"],
                    sent_via,
                    send_status,
                ),
            )

    _set_state("last_hourly_check", end)
    return {
        "window_start": start,
        "window_end": end,
        "sessions": sessions,
        "alerts": len(alerts),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "api_calls": api_calls,
        "retries": retries,
        "errors": errors,
        "api_cost_krw": api_cost,
    }
