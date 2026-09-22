import pandas as pd


def baseline_metrics(pre: pd.DataFrame) -> dict:
    df = pre.copy()
    if df.empty:
        return {"avg_monthly_inquiries": 0.0, "avg_handle_minutes": 0.0}
    created = pd.to_datetime(df["created_at"])
    months = created.dt.to_period("M")
    monthly = df.groupby(months).size()
    return {
        "avg_monthly_inquiries": float(monthly.mean()),
        "avg_handle_minutes": float(df["human_handle_minutes"].mean()),
    }


def chatbot_metrics(chat: pd.DataFrame) -> dict:
    if chat.empty:
        return {
            "sessions": 0,
            "resolution_rate": 0.0,
            "escalation_rate": 0.0,
            "no_api_rate": 0.0,
            "non_work_sessions": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "api_cost_krw": 0.0,
        }

    work = chat[chat["route"] != "NON_WORK"]
    resolution_rate = float(work["resolved"].mean() * 100) if not work.empty else 0.0
    escalation_rate = float(work["escalated"].mean() * 100) if not work.empty else 0.0
    no_api_rate = float(((chat["input_tokens"] + chat["output_tokens"]) == 0).mean() * 100)

    return {
        "sessions": int(len(chat)),
        "resolution_rate": resolution_rate,
        "escalation_rate": escalation_rate,
        "no_api_rate": no_api_rate,
        "non_work_sessions": int((chat["route"] == "NON_WORK").sum()),
        "input_tokens": int(chat["input_tokens"].sum()),
        "output_tokens": int(chat["output_tokens"].sum()),
        "api_cost_krw": float(chat["api_cost_krw"].sum()),
    }


def economic_metrics(
    chat: pd.DataFrame,
    pre: pd.DataFrame,
    hourly_cost: float,
    fixed_monthly_cost: float,
) -> dict:
    if chat.empty:
        return {
            "avoided_human_hours": 0.0,
            "saved_labor_cost_krw": 0.0,
            "chatbot_total_cost_krw": 0.0,
            "net_value_krw": 0.0,
        }

    baseline = baseline_metrics(pre)
    created = pd.to_datetime(chat["created_at"])
    months = max(created.dt.to_period("M").nunique(), 1)

    baseline_human_hours = (
        baseline["avg_monthly_inquiries"]
        * baseline["avg_handle_minutes"]
        * months
        / 60
    )
    post_human_hours = float(chat["human_handle_minutes"].sum() / 60)
    avoided_human_hours = max(baseline_human_hours - post_human_hours, 0.0)
    saved_labor_cost = avoided_human_hours * hourly_cost
    chatbot_total_cost = float(chat["api_cost_krw"].sum()) + fixed_monthly_cost * months

    return {
        "avoided_human_hours": avoided_human_hours,
        "saved_labor_cost_krw": saved_labor_cost,
        "chatbot_total_cost_krw": chatbot_total_cost,
        "net_value_krw": saved_labor_cost - chatbot_total_cost,
    }
