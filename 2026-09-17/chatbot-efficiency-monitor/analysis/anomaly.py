import pandas as pd


def find_inefficient_sessions(chat: pd.DataFrame) -> pd.DataFrame:
    if chat.empty:
        return chat.copy()

    df = chat.copy()
    total_tokens = df["input_tokens"] + df["output_tokens"]

    retry_mask = df["retry_count"].ge(2) if "retry_count" in df.columns else False
    error_mask = (
        (~df["status_code"].isin([0, 200])) if "status_code" in df.columns else False
    )

    mask = (
        (df["anomaly_flag"] == 1)
        | (df["route"] == "NON_WORK")
        | (df["resolution_seconds"] > 300)
        | (df["message_count"] >= 8)
        | (total_tokens >= 6000)
        | retry_mask
        | error_mask
    )

    preferred_cols = [
        "session_id",
        "created_at",
        "employee_id",
        "department",
        "category",
        "question_text",
        "route",
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
        "anomaly_flag",
    ]
    cols = [c for c in preferred_cols if c in df.columns]

    sort_cols = [c for c in ["anomaly_flag", "retry_count", "input_tokens"] if c in df.columns]
    ascending = [False] * len(sort_cols)
    return df.loc[mask, cols].sort_values(sort_cols, ascending=ascending)


def category_summary(chat: pd.DataFrame) -> pd.DataFrame:
    if chat.empty:
        return pd.DataFrame()

    work = chat[chat["route"] != "NON_WORK"].copy()
    if work.empty:
        return pd.DataFrame()

    agg = {
        "세션": ("session_id", "count"),
        "해결률": ("resolved", "mean"),
        "상담원전환율": ("escalated", "mean"),
        "평균해결초": ("resolution_seconds", "mean"),
        "평균대화횟수": ("message_count", "mean"),
        "평균입력토큰": ("input_tokens", "mean"),
    }
    if "retry_count" in work.columns:
        agg["평균재시도"] = ("retry_count", "mean")
    if "status_code" in work.columns:
        work["api_error"] = ~work["status_code"].isin([0, 200])
        agg["API오류율"] = ("api_error", "mean")

    out = work.groupby(["department", "category"]).agg(**agg).reset_index()
    out["해결률"] = (out["해결률"] * 100).round(1)
    out["상담원전환율"] = (out["상담원전환율"] * 100).round(1)
    out["평균해결초"] = out["평균해결초"].round(1)
    out["평균대화횟수"] = out["평균대화횟수"].round(1)
    out["평균입력토큰"] = out["평균입력토큰"].round(0)
    if "평균재시도" in out.columns:
        out["평균재시도"] = out["평균재시도"].round(2)
    if "API오류율" in out.columns:
        out["API오류율"] = (out["API오류율"] * 100).round(1)

    return out.sort_values(["해결률", "상담원전환율"], ascending=[True, False])
