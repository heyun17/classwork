# ====================================================================
# A4-M7 운영 대시보드 — streamlit run src/app_ops.py
# 읽는 파일: outputs/answer_log.jsonl, answer_eval.csv, ops_metrics.json, baseline.json, alerts.csv
# ====================================================================
import json

import pandas as pd
import streamlit as st

from config import OUT_DIR

st.set_page_config(page_title="A4-M7 RAG 운영 모니터링", layout="wide")
st.title("RAG Answer & Operations Monitoring")

need = ["answer_log.jsonl", "answer_eval.csv", "ops_metrics.json"]
missing = [f for f in need if not (OUT_DIR / f).exists()]
if missing:
    st.error(f"먼저 s09 → s10 → s11을 실행하세요. 없는 파일: {missing}")
    st.stop()

logs = pd.DataFrame([json.loads(l) for l in open(OUT_DIR / "answer_log.jsonl", encoding="utf-8")])
ev = pd.read_csv(OUT_DIR / "answer_eval.csv", encoding="utf-8-sig")
m = json.loads((OUT_DIR / "ops_metrics.json").read_text(encoding="utf-8"))
base_path = OUT_DIR / "baseline.json"
base = json.loads(base_path.read_text(encoding="utf-8")) if base_path.exists() else {}
alerts = pd.read_csv(OUT_DIR / "alerts.csv", encoding="utf-8-sig") if (OUT_DIR / "alerts.csv").exists() else pd.DataFrame()

if m["backend"] == "fake":
    st.warning("LLM_BACKEND=fake 결과입니다. 답변·시간·토큰은 흉내낸 값이라 품질 판단에 쓰지 마세요.")
st.caption(f"model={m['model']} · K={m['k']} · prompt={m['prompt_version']} · 요청 {m['requests']}건")


def delta(k, fmt="{:+.3f}"):
    if k in base and base[k] is not None and m.get(k) is not None:
        return fmt.format(m[k] - base[k])
    return None


tabs = st.tabs(["Overview", "Answer Quality", "Latency", "Token·Cost", "Reliability", "Drift·Mix", "Failures", "Alerts"])

with tabs[0]:
    c = st.columns(6)
    c[0].metric("검색 Hit", m["retrieval_hit"], delta("retrieval_hit"), help="정답 문서가 LLM에 넘긴 근거 안에 있었나")
    c[1].metric("근거성(규칙)", m["grounded_rule"], delta("grounded_rule"), help="답변의 숫자·코드가 근거에 모두 있나")
    c[2].metric("보류 정확도", m["abstention_accuracy"], delta("abstention_accuracy"), help="답할 수 없는 질문에서 보류한 비율")
    c[3].metric("E2E P95 (ms)", m["e2e_p95_ms"], delta("e2e_p95_ms", "{:+.0f}"), delta_color="inverse")
    c[4].metric("질문당 비용($)", f"{m['cost_per_q_usd']:.6f}", delta("cost_per_q_usd", "{:+.6f}"), delta_color="inverse")
    c[5].metric("오류율", m["error_rate"], delta("error_rate"), delta_color="inverse")
    st.subheader(f"Alert {len(alerts)}건")
    if len(alerts):
        st.dataframe(alerts, width="stretch", hide_index=True)
    else:
        st.success("기준을 벗어난 지표가 없습니다.")

with tabs[1]:
    st.subheader("판정 분포")
    st.bar_chart(ev["verdict"].value_counts())
    st.subheader("검색 × 답변 4분면 (답변 가능한 질문)")
    q = ev[ev["quadrant"].notna() & (ev["quadrant"] != "")]["quadrant"].value_counts().sort_index()
    st.dataframe(q.rename("건수"), width="stretch")
    st.caption("③ 검색X·답변O가 가장 위험: 정답 문서 없이 그럴듯하게 답한 경우")

with tabs[2]:
    lat = logs[logs["error"].isna()][["query_id", "retrieval_ms", "prompt_ms", "llm_ms", "e2e_ms"]]
    st.dataframe(pd.DataFrame({
        "avg": [m["retrieval_avg_ms"], m["llm_avg_ms"], m["e2e_avg_ms"]],
        "p50": [m["retrieval_p50_ms"], m["llm_p50_ms"], m["e2e_p50_ms"]],
        "p95": [m["retrieval_p95_ms"], m["llm_p95_ms"], m["e2e_p95_ms"]],
        "p99": [m["retrieval_p99_ms"], m["llm_p99_ms"], m["e2e_p99_ms"]],
    }, index=["검색", "LLM", "End-to-End"]), width="stretch")
    st.subheader("질문별 단계 시간 (ms)")
    st.bar_chart(lat.set_index("query_id")[["retrieval_ms", "prompt_ms", "llm_ms"]])

with tabs[3]:
    c = st.columns(4)
    c[0].metric("평균 Context(자)", m["avg_context_chars"])
    c[1].metric("평균 Input token", m["avg_input_tokens"], delta("avg_input_tokens", "{:+.0f}"), delta_color="inverse")
    c[2].metric("평균 Output token", m["avg_output_tokens"])
    c[3].metric("1,000건당(원)", m["cost_per_1000q_krw"])
    st.bar_chart(logs.set_index("query_id")[["input_tokens", "output_tokens"]])

with tabs[4]:
    c = st.columns(3)
    c[0].metric("오류율", m["error_rate"])
    c[1].metric("재시도율", m["retry_rate"])
    c[2].metric("복구율", m["recovery_rate"])
    st.dataframe(logs[(logs["retries"] > 0) | logs["error"].notna()][["query_id", "retries", "error"]],
                 width="stretch", hide_index=True)

with tabs[5]:
    st.subheader("질문 유형 분포")
    st.bar_chart(logs["query_type"].value_counts())
    if base:
        st.subheader("기준선과 비교")
        keys = ["retrieval_hit", "grounded_rule", "citation_valid", "abstention_accuracy",
                "avg_input_tokens", "cost_per_q_usd", "e2e_p95_ms", "error_rate"]
        st.dataframe(pd.DataFrame({"기준선": [base.get(k) for k in keys], "현재": [m.get(k) for k in keys]}, index=keys),
                     width="stretch")

with tabs[6]:
    bad = ev[ev["verdict"] != "PASS"]
    st.write(f"PASS가 아닌 질문 {len(bad)}건")
    pick = st.selectbox("질문 선택", bad["query_id"].tolist() or ["-"])
    if pick != "-":
        row = logs[logs["query_id"] == pick].iloc[0]
        e = ev[ev["query_id"] == pick].iloc[0]
        st.markdown(f"**{row['question']}**  ·  판정 `{e['verdict']}`")
        st.write("정답 문서:", row["relevant_doc_ids"], " / 넘긴 근거:", row["context_doc_ids"])
        st.text_area("답변", row["answer"], height=90)
        st.text_area("LLM에 넘긴 근거", row["context"], height=220)

with tabs[7]:
    st.dataframe(alerts if len(alerts) else pd.DataFrame({"메시지": ["Alert 없음"]}), width="stretch", hide_index=True)
    st.caption("규칙은 src/config_ops.py 의 ALERT_ABS(절대 기준), ALERT_REL(기준선 대비)")
