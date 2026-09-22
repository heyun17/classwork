from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.db import read_table
from analysis.metrics import baseline_metrics, chatbot_metrics, economic_metrics
from analysis.anomaly import find_inefficient_sessions, category_summary
from monitoring.config import MONITOR_INTERVAL_SECONDS
from monitoring.live_store import (
    pending_live_count,
    read_alert_history,
    read_employee_snapshots,
    read_hourly_snapshots,
)

st.set_page_config(page_title="사내 챗봇 효율 모니터", page_icon="🤖", layout="wide")


@st.cache_data
def load_data():
    return {
        "pre": read_table("pre_chatbot_inquiries"),
        "chat": read_table("chatbot_logs"),
        "faq": read_table("faq"),
        "system": read_table("system_metrics"),
        "profile": read_table("company_profile"),
    }


def won(v):
    return f"₩{v:,.0f}"


def _render_live_monitoring_body() -> None:
    snapshots = read_hourly_snapshots(limit=168)
    alerts = read_alert_history(limit=100)
    pending = pending_live_count()

    st.caption(
        f"직원 챗봇 사용 로그는 즉시 DB에 저장되고, 현재 {MONITOR_INTERVAL_SECONDS}초 주기로 집계되어 이 화면에 반영됩니다."
    )
    if MONITOR_INTERVAL_SECONDS == 60:
        st.warning(
            "현재 개발 테스트 모드: 1분 주기입니다. 발표/운영에서 1시간으로 바꾸려면 "
            "monitoring/config.py의 MONITOR_INTERVAL_SECONDS = 60 을 3600으로 변경하세요."
        )

    if snapshots.empty:
        st.info(
            "아직 집계 결과가 없습니다. 별도 터미널에서 `python scripts/hourly_monitor.py`를 실행한 뒤 "
            "직원용 챗봇을 사용하거나 개발용 로그를 생성하세요."
        )
        st.metric("아직 집계되지 않은 실시간 로그", f"{pending:,}건")
        return

    latest = snapshots.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("최근 반영 세션", f"{int(latest['sessions']):,}")
    c2.metric("최근 Token", f"{int(latest['input_tokens'] + latest['output_tokens']):,}")
    c3.metric("API 호출", f"{int(latest['api_calls']):,}")
    c4.metric("재시도", f"{int(latest['retries']):,}")
    c5.metric("API 오류", f"{int(latest['errors']):,}")
    c6.metric("이상치 알림", f"{int(latest['anomaly_count']):,}")

    st.caption(
        f"최근 반영 구간: {latest['window_start']} ~ {latest['window_end']} · "
        f"다음 집계를 기다리는 원본 로그: {pending:,}건"
    )

    timeline = snapshots.sort_values("window_end").copy()
    timeline["window_end"] = pd.to_datetime(timeline["window_end"])
    timeline["total_tokens"] = timeline["input_tokens"] + timeline["output_tokens"]

    left, right = st.columns(2)
    with left:
        st.subheader("주기별 세션 / 오류")
        st.line_chart(timeline.set_index("window_end")[["sessions", "errors", "retries"]])
    with right:
        st.subheader("주기별 Token")
        st.line_chart(timeline.set_index("window_end")[["total_tokens"]])

    st.subheader("최근 반영 구간 직원별 사용")
    employee = read_employee_snapshots(window_end=str(latest["window_end"]), limit=200)
    if employee.empty:
        st.caption("최근 구간에 직원별 집계 데이터가 없습니다.")
    else:
        show = employee[
            [
                "employee_id",
                "department",
                "sessions",
                "total_tokens",
                "api_calls",
                "retries",
                "errors",
                "resolved",
                "api_cost_krw",
            ]
        ].copy()
        show.columns = [
            "직원ID",
            "문의부서",
            "세션",
            "총Token",
            "API호출",
            "재시도",
            "오류",
            "해결건",
            "API비용",
        ]
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.caption(
            "직원 Token이 많아도 개인 문제로 단정하지 않습니다. 세션 수, 세션당 Token, 재시도, 오류, 문의 종류를 함께 확인합니다."
        )

    st.subheader("이상치 / 운영 알림")
    if alerts.empty:
        st.success("기록된 이상치 알림이 없습니다.")
    else:
        alert_view = alerts[
            [
                "created_at",
                "severity",
                "alert_type",
                "employee_id",
                "message",
                "sent_via",
                "send_status",
            ]
        ].copy()
        alert_view.columns = ["발생시각", "등급", "유형", "직원ID", "내용", "알림수단", "전송상태"]
        st.dataframe(alert_view, use_container_width=True, hide_index=True)
        st.caption(
            "ALERT_WEBHOOK_URL을 설정하면 Webhook(Slack 등)을 우선 사용하고, 미설정/실패 시 이메일을 시도합니다. "
            "둘 다 없으면 알림 내용은 DB에만 기록됩니다."
        )


# Streamlit 1.40+의 fragment를 사용해 이 패널만 주기적으로 다시 읽는다.
# 주기는 monitoring/config.py 한 곳에서 관리한다.
@st.fragment(run_every=MONITOR_INTERVAL_SECONDS)
def render_live_monitoring() -> None:
    _render_live_monitoring_body()


data = load_data()
pre = data["pre"]
chat = data["chat"]
faq = data["faq"]
system = data["system"]
profile = dict(zip(data["profile"]["key"], data["profile"]["value"]))

chat["created_at"] = pd.to_datetime(chat["created_at"])
chat["month"] = chat["created_at"].dt.to_period("M").astype(str)
pre["created_at"] = pd.to_datetime(pre["created_at"])
pre["month"] = pre["created_at"].dt.to_period("M").astype(str)

st.title("🤖 사내 챗봇 비용 · 자원 절감 모니터링")
st.caption("가상회사 GaonWorks Services의 실습용 데이터입니다. 비용 단가는 실제 계약 요금이 아닌 프로젝트 가정값입니다.")

with st.sidebar:
    st.markdown("### 실시간 운영")
    st.caption(f"집계/화면 갱신 주기: {MONITOR_INTERVAL_SECONDS}초")
    st.caption("직원 챗봇 원본 로그는 사용 즉시 DB에 저장됩니다.")

month_options = ["전체"] + sorted(chat["month"].unique().tolist())
selected_month = st.sidebar.selectbox("분석 월", month_options)
departments = ["전체"] + sorted(chat["department"].unique().tolist())
selected_dep = st.sidebar.selectbox("부서", departments)

filtered = chat.copy()
if selected_month != "전체":
    filtered = filtered[filtered["month"] == selected_month]
if selected_dep != "전체":
    filtered = filtered[filtered["department"] == selected_dep]

hourly_cost = float(profile.get("hourly_labor_cost_krw", 35000))
fixed_monthly = float(profile.get("fixed_chatbot_infra_cost_monthly_krw", 800000))
base = baseline_metrics(pre)
metrics = chatbot_metrics(filtered)
econ = economic_metrics(filtered, pre, hourly_cost=hourly_cost, fixed_monthly_cost=fixed_monthly)

tabs = st.tabs(["실시간 운영", "요약", "효율 분석", "비용/토큰", "이상치", "시스템 상태", "데이터"])

with tabs[0]:
    st.subheader("실시간 로그 → 주기별 운영 모니터링")
    render_live_monitoring()

with tabs[1]:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("챗봇 세션", f"{metrics['sessions']:,}")
    c2.metric("업무질문 해결률", f"{metrics['resolution_rate']:.1f}%")
    c3.metric("상담원 전환율", f"{metrics['escalation_rate']:.1f}%")
    c4.metric("API 미사용 비율", f"{metrics['no_api_rate']:.1f}%")
    c5.metric("비업무 질문", f"{metrics['non_work_sessions']:,}")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("기존 월평균 사람 문의", f"{base['avg_monthly_inquiries']:.0f}건")
    d2.metric("기존 평균 처리시간", f"{base['avg_handle_minutes']:.1f}분")
    d3.metric("대체된 추정 인적시간", f"{econ['avoided_human_hours']:.1f}시간")
    d4.metric("추정 순가치", won(econ["net_value_krw"]))

    st.subheader("월별 문의량 변화")
    pre_month = pre.groupby("month").size().rename("도입 전 사람 문의")
    post_month = chat.groupby("month").size().rename("도입 후 챗봇 세션")
    volume = pd.concat([pre_month, post_month], axis=1).fillna(0)
    st.bar_chart(volume)

    st.info("핵심 해석: 도입 후 챗봇 세션 수가 기존 사람 문의보다 크게 늘어도 실패가 아닙니다. 해결률, 상담원 전환, 처리시간, API 비용을 함께 봐야 실제 효율을 판단할 수 있습니다.")

with tabs[2]:
    st.subheader("부서별 효율")
    work = filtered[filtered["route"] != "NON_WORK"]
    dep = work.groupby("department").agg(
        세션=("session_id", "count"),
        해결률=("resolved", "mean"),
        상담원전환율=("escalated", "mean"),
        평균해결초=("resolution_seconds", "mean"),
        평균대화횟수=("message_count", "mean"),
    )
    dep["해결률"] = (dep["해결률"] * 100).round(1)
    dep["상담원전환율"] = (dep["상담원전환율"] * 100).round(1)
    st.dataframe(dep, use_container_width=True)
    st.subheader("카테고리별 개선 우선 후보")
    cat = category_summary(filtered)
    st.dataframe(cat.head(15), use_container_width=True)

with tabs[3]:
    st.subheader("토큰/API 비용")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input tokens", f"{metrics['input_tokens']:,}")
    c2.metric("Output tokens", f"{metrics['output_tokens']:,}")
    c3.metric("API 변동비", won(metrics["api_cost_krw"]))
    c4.metric("총 챗봇 비용(고정비 포함)", won(econ["chatbot_total_cost_krw"]))

    route = filtered.groupby("route").agg(
        세션=("session_id", "count"),
        input_tokens=("input_tokens", "sum"),
        output_tokens=("output_tokens", "sum"),
        api_cost_krw=("api_cost_krw", "sum"),
    ).sort_values("세션", ascending=False)
    st.dataframe(route, use_container_width=True)

    st.success(f"FAQ/메뉴/보안차단/명백한 잡담 차단을 먼저 처리해 현재 선택 데이터의 {metrics['no_api_rate']:.1f}%는 LLM API를 사용하지 않습니다.")
    st.caption("업무 여부가 애매한 질문은 차단하지 않고 API 처리 대상으로 넘깁니다. 실운영에서는 모델별 실제 가격표와 인프라/로그/DB 비용을 반영해야 합니다.")

    st.subheader("직원별 토큰 사용 상위")
    employee = filtered.groupby("employee_id").agg(
        세션=("session_id", "count"),
        입력토큰=("input_tokens", "sum"),
        출력토큰=("output_tokens", "sum"),
        API호출=("api_call_count", "sum"),
        재시도=("retry_count", "sum"),
        해결률=("resolved", "mean"),
    )
    employee["총토큰"] = employee["입력토큰"] + employee["출력토큰"]
    employee["해결률"] = (employee["해결률"] * 100).round(1)
    st.dataframe(employee.sort_values("총토큰", ascending=False).head(20), use_container_width=True)

with tabs[4]:
    st.subheader("비효율/이상치 세션")
    anomalies = find_inefficient_sessions(filtered)
    st.metric("감지 건수", f"{len(anomalies):,}")
    st.dataframe(anomalies.head(200), use_container_width=True)
    st.caption("데모 기준: 비업무 질문, 비정상적으로 긴 해결시간, 과도한 대화 횟수, 높은 토큰 사용 등을 후보로 표시합니다. 실제 운영에서는 조직별 정상범위를 학습해 기준을 조정합니다.")

with tabs[5]:
    st.subheader("시스템 엔지니어 관점 상태")
    sysdf = system.copy()
    sysdf["date"] = pd.to_datetime(sysdf["date"])
    st.line_chart(sysdf.set_index("date")[["cpu_pct", "memory_pct"]])
    st.line_chart(sysdf.set_index("date")[["api_latency_ms"]])
    incidents = sysdf[sysdf["status"] != "normal"]
    st.dataframe(incidents, use_container_width=True)

    if {"retry_count", "status_code", "error_type"}.issubset(filtered.columns):
        st.subheader("API 오류/재시도")
        retry_sessions = int((filtered["retry_count"] > 0).sum())
        final_errors = int((~filtered["status_code"].isin([0, 200])).sum())
        extra_calls = int(filtered["retry_count"].sum())
        e1, e2, e3 = st.columns(3)
        e1.metric("재시도 발생 세션", f"{retry_sessions:,}")
        e2.metric("최종 API 오류", f"{final_errors:,}")
        e3.metric("재시도로 늘어난 호출", f"{extra_calls:,}")

        err = filtered[filtered["error_type"].fillna("") != ""]
        if not err.empty:
            err_summary = err.groupby("error_type").agg(
                세션=("session_id", "count"),
                재시도=("retry_count", "sum"),
                추가토큰=("input_tokens", "sum"),
            ).sort_values("세션", ascending=False)
            st.dataframe(err_summary, use_container_width=True)

    st.caption("자원 사용률은 핵심 성과지표가 아니라 장애 원인 확인용 보조지표로 배치했습니다. API 오류와 재시도는 불필요한 호출/토큰 증가 원인이 될 수 있으므로 함께 확인합니다.")

with tabs[6]:
    st.subheader("원본 데이터 미리보기")
    dataset = st.selectbox("데이터셋", ["chatbot_logs", "pre_chatbot_inquiries", "faq", "system_metrics", "company_profile"])
    mapping = {
        "chatbot_logs": chat,
        "pre_chatbot_inquiries": pre,
        "faq": faq,
        "system_metrics": system,
        "company_profile": data["profile"],
    }
    st.dataframe(mapping[dataset].head(500), use_container_width=True)
