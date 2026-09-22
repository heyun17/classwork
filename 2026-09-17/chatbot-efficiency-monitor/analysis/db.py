from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "chatbot_monitor.db"


def read_table(table_name: str) -> pd.DataFrame:
    allowed = {
        "pre_chatbot_inquiries",
        "chatbot_logs",
        "faq",
        "system_metrics",
        "company_profile",
    }
    if table_name not in allowed:
        raise ValueError(f"허용되지 않은 테이블입니다: {table_name}")
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
