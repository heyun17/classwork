from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "chatbot_monitor.db"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    chat = pd.read_sql_query("SELECT * FROM chatbot_logs", conn)

chat["created_at"] = pd.to_datetime(chat["created_at"])
chat["month"] = chat["created_at"].dt.to_period("M").astype(str)
chat["total_tokens"] = chat["input_tokens"] + chat["output_tokens"]
chat["api_error"] = ~chat["status_code"].isin([0, 200])

monthly = chat.groupby("month").agg(
    sessions=("session_id", "count"),
    resolved=("resolved", "sum"),
    escalated=("escalated", "sum"),
    input_tokens=("input_tokens", "sum"),
    output_tokens=("output_tokens", "sum"),
    api_calls=("api_call_count", "sum"),
    retries=("retry_count", "sum"),
    api_errors=("api_error", "sum"),
    api_cost_krw=("api_cost_krw", "sum"),
).reset_index()
monthly.to_csv(OUT / "monthly_summary.csv", index=False, encoding="utf-8-sig")

department = chat.groupby("department").agg(
    sessions=("session_id", "count"),
    resolution_rate=("resolved", "mean"),
    escalation_rate=("escalated", "mean"),
    total_tokens=("total_tokens", "sum"),
    retries=("retry_count", "sum"),
    api_errors=("api_error", "sum"),
    api_cost_krw=("api_cost_krw", "sum"),
).reset_index()
department["resolution_rate"] = (department["resolution_rate"] * 100).round(1)
department["escalation_rate"] = (department["escalation_rate"] * 100).round(1)
department.to_csv(OUT / "department_summary.csv", index=False, encoding="utf-8-sig")

route = chat.groupby("route").agg(
    sessions=("session_id", "count"),
    input_tokens=("input_tokens", "sum"),
    output_tokens=("output_tokens", "sum"),
    api_calls=("api_call_count", "sum"),
    api_cost_krw=("api_cost_krw", "sum"),
).reset_index().sort_values("sessions", ascending=False)
route.to_csv(OUT / "route_summary.csv", index=False, encoding="utf-8-sig")

anomaly = chat[
    (chat["anomaly_flag"] == 1)
    | (chat["retry_count"] >= 2)
    | (chat["api_error"])
    | (chat["total_tokens"] >= 6000)
].sort_values(["anomaly_flag", "total_tokens"], ascending=[False, False])
anomaly.to_csv(OUT / "anomaly_sessions.csv", index=False, encoding="utf-8-sig")

print(f"리포트 생성 완료: {OUT}")
