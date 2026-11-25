# ====================================================================
# Step 09 · 품질 모니터링 Dashboard — 실행: streamlit run src/app_dashboard.py
# outputs/의 CSV를 읽어 보여 준다. 08까지 먼저 실행해야 한다.
# ====================================================================
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from config import OUT_DIR, K_LIST, CHUNK_METHODS, DEFAULT_CHUNK_METHOD, HYBRID_WEIGHTS
from common import load_golden, load_chunks

st.set_page_config(page_title="RAG Retrieval Quality", layout="wide")
st.title("RAG Data & Retrieval Quality Monitor")
st.caption("추천값은 현재 샘플 문서 16개와 Golden 질문 20개에 대한 결과입니다.")

summary = pd.read_csv(OUT_DIR / "evaluation_summary.csv")
pq = pd.read_csv(OUT_DIR / "evaluation_by_query.csv")
stats = pd.read_csv(OUT_DIR / "chunk_stats.csv")
golden = load_golden()

with st.sidebar:
    retriever = st.selectbox("검색 방식", sorted(summary.retriever.unique()))
    method = st.selectbox("청킹 방식", CHUNK_METHODS, index=CHUNK_METHODS.index(DEFAULT_CHUNK_METHOD))
    k = st.select_slider("K", options=K_LIST, value=3)
    st.caption(f"Hybrid 가중치: {HYBRID_WEIGHTS}")

tabs = st.tabs(["Overview", "Chunk Monitor", "Golden Dataset", "K Experiment",
                "Chunking Experiment", "Query Type", "Failure Analysis", "Recommendation"])
row = summary[(summary.retriever == retriever) & (summary.chunk_method == method) & (summary.K == k)].iloc[0]

with tabs[0]:
    c = st.columns(4)
    c[0].metric("문서 수", 16); c[1].metric("청크 수", int(stats[stats.chunk_method == method].chunks.iloc[0]))
    c[2].metric("Golden 질문", len(golden)); c[3].metric("평균 Latency(ms)", f'{row.latency_ms:.2f}')
    c = st.columns(5)
    for col, (name, key, help_) in zip(c, [("Precision@K", "precision", "가져온 문서 중 정답 비율"),
                                           ("Recall@K", "recall", "찾아야 할 정답을 얼마나 놓치지 않았나"),
                                           ("Hit Rate@K", "hit", "정답이 하나라도 들어온 질문 비율"),
                                           ("MRR", "mrr", "첫 정답이 몇 등인지(1/순위) 평균"),
                                           ("nDCG@K", "ndcg", "정답이 위쪽에 있을수록 높음")]):
        col.metric(name, f"{row[key]:.3f}", help=help_)

with tabs[1]:
    st.dataframe(stats, hide_index=True, width="stretch")
    chunks = pd.DataFrame(load_chunks(method))
    st.plotly_chart(px.histogram(chunks, x="char_count", nbins=20, title=f"Chunk Size Distribution · {method}"),
                    width="stretch")
    doc = st.selectbox("원문 ↔ 청크 비교", chunks.doc_id.unique())
    for _, ch in chunks[chunks.doc_id == doc].iterrows():
        st.text(f'[{ch.chunk_id}] {ch.char_count}자\n{ch.content}')

with tabs[2]:
    st.dataframe(pd.DataFrame(golden), hide_index=True, width="stretch")

with tabs[3]:
    sub = summary[(summary.chunk_method == method)]
    m = st.selectbox("지표", ["precision", "recall", "hit", "mrr", "ndcg", "context_chars", "latency_ms"])
    st.plotly_chart(px.line(sub, x="K", y=m, color="retriever", markers=True), width="stretch")
    st.dataframe(sub, hide_index=True, width="stretch")

with tabs[4]:
    sub = summary[summary.K == k]
    st.plotly_chart(px.bar(sub, x="chunk_method", y="hit", color="retriever", barmode="group",
                           title=f"청킹 방식별 Hit Rate@{k}"), width="stretch")
    st.dataframe(sub, hide_index=True, width="stretch")

with tabs[5]:
    bt = pd.read_csv(OUT_DIR / "evaluation_by_type.csv")
    st.plotly_chart(px.bar(bt, x="query_type", y="hit", color="retriever", barmode="group",
                           title="질문 유형별 Hit Rate (heading, K=3)"), width="stretch")

with tabs[6]:
    fails = pd.read_csv(OUT_DIR / "failure_cases.csv")
    st.dataframe(fails[["retriever", "query_id", "query_type", "question", "relevant_docs", "top_k_docs"]],
                 hide_index=True, width="stretch")
    st.dataframe(pd.read_csv(OUT_DIR / "over_retrieved.csv"), hide_index=True, width="stretch")

with tabs[7]:
    st.caption("규칙: Recall@K ≥ 0.9 이고 Hit Rate@K ≥ 0.95 인 조합 중 → K가 가장 작고 → nDCG가 높고 → Context가 작은 것")
    ok = summary[(summary.recall >= 0.9) & (summary.hit >= 0.95)]
    if ok.empty:
        st.warning("조건을 만족하는 조합이 없습니다. 기준을 낮추거나 검색 방식을 개선하세요.")
    else:
        best = ok.sort_values(["K", "ndcg", "context_chars"], ascending=[True, False, True]).iloc[0]
        st.success(f"추천: {best.retriever} · {best.chunk_method} · K={int(best.K)}  "
                   f"(Recall {best.recall:.3f}, Hit {best.hit:.3f}, nDCG {best.ndcg:.3f}, Context {best.context_chars:.0f}자)")
        st.dataframe(ok.sort_values(["K", "ndcg"], ascending=[True, False]).head(10), hide_index=True, width="stretch")
    st.caption("K를 키우면 Recall은 오르지만 LLM에 넘길 Context가 커집니다. 추천값은 현재 Golden Dataset 기준입니다.")
