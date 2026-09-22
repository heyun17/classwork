from pathlib import Path
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monitoring.live_store import ensure_live_tables

DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "database" / "chatbot_monitor.db"
TABLES = {
    "pre_chatbot_inquiries": "pre_chatbot_inquiries.csv",
    "chatbot_logs": "chatbot_logs.csv",
    "faq": "faq.csv",
    "system_metrics": "system_metrics.csv",
    "company_profile": "company_profile.csv",
}

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    for table, filename in TABLES.items():
        df = pd.read_csv(DATA_DIR / filename)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"{table}: {len(df):,} rows")

# 실시간 모니터링용 테이블도 함께 준비한다.
ensure_live_tables()
print(f"DB 생성 완료: {DB_PATH}")
