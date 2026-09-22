from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sqlite3
import uuid

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "chatbot_monitor.db"

LIVE_COLUMNS = [
    "session_id",
    "created_at",
    "employee_id",
    "department",
    "category",
    "question_text",
    "question_type",
    "route",
    "api_required",
    "resolved",
    "escalated",
    "resolution_seconds",
    "message_count",
    "input_tokens",
    "output_tokens",
    "api_call_count",
    "retry_count",
    "status_code",
    "error_type",
    "api_cost_krw",
    "human_handle_minutes",
    "anomaly_flag",
]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if column not in _table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def ensure_live_tables() -> None:
    """실시간 로그/주기별 집계/알림 테이블을 만든다.

    기존 DB가 있어도 필요한 새 컬럼만 추가해 데이터 손실 없이 사용할 수 있다.
    """
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS live_chatbot_logs (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                department TEXT NOT NULL,
                category TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                route TEXT NOT NULL,
                api_required INTEGER NOT NULL DEFAULT 0,
                resolved INTEGER NOT NULL DEFAULT 0,
                escalated INTEGER NOT NULL DEFAULT 0,
                resolution_seconds REAL NOT NULL DEFAULT 0,
                message_count INTEGER NOT NULL DEFAULT 1,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                api_call_count INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                status_code INTEGER NOT NULL DEFAULT 0,
                error_type TEXT,
                api_cost_krw REAL NOT NULL DEFAULT 0,
                human_handle_minutes REAL NOT NULL DEFAULT 0,
                anomaly_flag INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_live_created_at
                ON live_chatbot_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_live_employee
                ON live_chatbot_logs(employee_id, created_at);

            CREATE TABLE IF NOT EXISTS hourly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                sessions INTEGER NOT NULL,
                resolved INTEGER NOT NULL,
                escalated INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                api_calls INTEGER NOT NULL DEFAULT 0,
                retries INTEGER NOT NULL DEFAULT 0,
                errors INTEGER NOT NULL DEFAULT 0,
                non_work_sessions INTEGER NOT NULL DEFAULT 0,
                api_cost_krw REAL NOT NULL,
                anomaly_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hourly_employee_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                department TEXT NOT NULL,
                sessions INTEGER NOT NULL,
                resolved INTEGER NOT NULL,
                api_calls INTEGER NOT NULL,
                retries INTEGER NOT NULL,
                errors INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                api_cost_krw REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_emp_snapshot_window
                ON hourly_employee_snapshots(window_end, employee_id);

            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                severity TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                employee_id TEXT,
                message TEXT NOT NULL,
                sent_via TEXT NOT NULL DEFAULT 'record_only',
                send_status TEXT NOT NULL DEFAULT 'not_sent'
            );

            CREATE TABLE IF NOT EXISTS monitor_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

        # 이전 버전 DB를 그대로 사용하는 경우를 위한 간단한 마이그레이션.
        _ensure_column(conn, "live_chatbot_logs", "api_required", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "hourly_snapshots", "api_calls", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "hourly_snapshots", "retries", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "hourly_snapshots", "errors", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "hourly_snapshots", "non_work_sessions", "INTEGER NOT NULL DEFAULT 0")


def new_session_id() -> str:
    return f"LIVE-{uuid.uuid4().hex[:16].upper()}"


def sanitize_question_text(text: str, max_length: int = 200) -> str:
    """로그에 개인정보가 그대로 남는 위험을 줄이기 위한 최소 마스킹.

    실제 회사에서는 개인정보/기밀정보 분류 정책에 맞춰 더 강한 마스킹을 적용한다.
    """
    value = str(text or "").strip()
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", value)
    value = re.sub(r"\b\d{6,}\b", "[NUMBER]", value)
    return value[:max_length]


def log_chat_usage(
    *,
    employee_id: str,
    department: str,
    category: str,
    question_text: str,
    question_type: str,
    route: str,
    api_required: int = 0,
    resolved: int = 0,
    escalated: int = 0,
    resolution_seconds: float = 0.0,
    message_count: int = 1,
    input_tokens: int = 0,
    output_tokens: int = 0,
    api_call_count: int = 0,
    retry_count: int = 0,
    status_code: int = 0,
    error_type: str | None = None,
    api_cost_krw: float = 0.0,
    human_handle_minutes: float = 0.0,
    anomaly_flag: int = 0,
    session_id: str | None = None,
    created_at: str | None = None,
) -> str:
    """챗봇 사용 1건을 SQLite에 즉시 저장한다.

    실제 LLM 연동 시 모델 응답의 usage 메타데이터에서 input/output token을 받아
    이 함수에 전달한다. 현재 데모는 실제 LLM API를 호출하지 않으므로
    LLM_REQUIRED 질문도 api_required=1로만 기록하고 token/api_call_count는 0이다.
    """
    ensure_live_tables()
    sid = session_id or new_session_id()
    ts = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    values = (
        sid,
        ts,
        str(employee_id).strip() or "DEMO-USER",
        str(department).strip() or "미분류",
        str(category).strip() or "미분류",
        sanitize_question_text(question_text),
        str(question_type),
        str(route),
        int(api_required),
        int(resolved),
        int(escalated),
        float(resolution_seconds),
        int(message_count),
        int(input_tokens),
        int(output_tokens),
        int(api_call_count),
        int(retry_count),
        int(status_code),
        error_type,
        float(api_cost_krw),
        float(human_handle_minutes),
        int(anomaly_flag),
    )

    with _connect() as conn:
        placeholders = ",".join(["?"] * len(LIVE_COLUMNS))
        conn.execute(
            f"INSERT INTO live_chatbot_logs ({','.join(LIVE_COLUMNS)}) VALUES ({placeholders})",
            values,
        )
    return sid


def read_live_logs(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    ensure_live_tables()
    query = "SELECT * FROM live_chatbot_logs WHERE 1=1"
    params: list[str] = []
    if start:
        query += " AND created_at > ?"
        params.append(start)
    if end:
        query += " AND created_at <= ?"
        params.append(end)
    query += " ORDER BY created_at"
    with _connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def latest_snapshot_end() -> str | None:
    ensure_live_tables()
    with _connect() as conn:
        row = conn.execute(
            "SELECT window_end FROM hourly_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else None


def read_hourly_snapshots(limit: int = 168) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM hourly_snapshots ORDER BY id DESC LIMIT ?",
            conn,
            params=(int(limit),),
        )


def read_employee_snapshots(window_end: str | None = None, limit: int = 500) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        if window_end:
            return pd.read_sql_query(
                """
                SELECT * FROM hourly_employee_snapshots
                WHERE window_end = ?
                ORDER BY total_tokens DESC, sessions DESC
                LIMIT ?
                """,
                conn,
                params=(window_end, int(limit)),
            )
        return pd.read_sql_query(
            "SELECT * FROM hourly_employee_snapshots ORDER BY id DESC LIMIT ?",
            conn,
            params=(int(limit),),
        )


def read_alert_history(limit: int = 200) -> pd.DataFrame:
    ensure_live_tables()
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM alert_history ORDER BY id DESC LIMIT ?",
            conn,
            params=(int(limit),),
        )


def pending_live_count() -> int:
    """아직 주기 집계에 반영되지 않은 원본 로그 수."""
    ensure_live_tables()
    cutoff = latest_snapshot_end()
    with _connect() as conn:
        if cutoff:
            row = conn.execute(
                "SELECT COUNT(*) FROM live_chatbot_logs WHERE created_at > ?", (cutoff,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM live_chatbot_logs").fetchone()
    return int(row[0]) if row else 0
