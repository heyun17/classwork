# ====================================================================
# 파일 용도: Part 1의 최종 Streamlit 업무 화면을 실행합니다.
# OpenSearch의 실제 sales 데이터와 저장된 FAISS 내부문서를 함께 사용합니다.
# ====================================================================

import pandas as pd
import streamlit as st

from clients import (
    get_openai_client,
    get_opensearch_client,
)
from faiss_service import (
    load_faiss,
    search_faiss,
)
from sales_service import (
    get_regions,
    get_region_summary,
    get_region_documents,
)
from rag_service import hybrid_answer


st.set_page_config(
    page_title="Regional Sales Intelligence",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.block-container {padding-top:1.2rem; padding-bottom:2rem;}
[data-testid="stMetric"] {
    border:1px solid #e3e8ee;
    border-radius:14px;
    padding:14px 16px;
    background:#ffffff;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_clients():
    return (
        get_openai_client(),
        get_opensearch_client()
    )


@st.cache_resource
def load_vector_db():
    return load_faiss()


@st.cache_data(ttl=30)
def load_regions():
    _, os_client = load_clients()
    return sorted(get_regions(os_client))


@st.cache_data(ttl=30)
def load_region_documents(region):
    _, os_client = load_clients()
    return get_region_documents(
        os_client,
        region
    )


try:
    openai_client, os_client = load_clients()
    faiss_index, chunks = load_vector_db()
    regions = load_regions()

except Exception as e:
    st.error(f"초기화 오류: {e}")
    st.info(
        "Docker의 OpenSearch 실행 상태, .env, "
        "rag_faiss/index.faiss 및 chunks.json을 확인하세요."
    )
    st.stop()


with st.sidebar:
    st.header("조회 조건")

    region = st.selectbox(
        "지역",
        regions
    )

    top_k = st.slider(
        "RAG 검색 문서 수",
        min_value=1,
        max_value=min(5, faiss_index.ntotal),
        value=min(3, faiss_index.ntotal)
    )

    if st.button("데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(
        "OpenSearch와 OpenSearch Dashboards가 "
        "Docker에서 실행 중이어야 합니다."
    )


summary = get_region_summary(
    os_client,
    region
)

orders_df = load_region_documents(
    region
)


st.title("Regional Sales Intelligence")
st.caption(
    "OpenSearch Sales + FAISS Knowledge + GPT-4.1-nano"
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "총 매출",
    f'{summary["total_revenue"]:,.0f}원'
)

c2.metric(
    "주문 건수",
    f'{summary["order_count"]:,}건'
)

c3.metric(
    "판매 수량",
    f'{summary["total_quantity"]:,.0f}개'
)

satisfaction = (
    summary["avg_satisfaction"]
    if summary["avg_satisfaction"] is not None
    else 0
)

c4.metric(
    "평균 만족도",
    f"{satisfaction:.2f}"
)


tab1, tab2, tab3 = st.tabs([
    "Sales Overview",
    "AI Analysis",
    "Evidence"
])


with tab1:
    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("월별 매출 추이")

        if not orders_df.empty:
            monthly = (
                orders_df
                .set_index("order_date")
                .resample("MS")["revenue"]
                .sum()
            )
            st.line_chart(
                monthly,
                height=320
            )
        else:
            st.info("선택 지역의 주문 데이터가 없습니다.")

    with right:
        st.subheader("제품별 매출")

        product_rows = pd.DataFrame([
            {
                "제품": item["key"],
                "매출": item["sales"]["value"]
            }
            for item in summary["product_sales"]
        ])

        if not product_rows.empty:
            st.bar_chart(
                product_rows.set_index("제품"),
                height=320
            )

    lower_left, lower_right = st.columns(2)

    with lower_left:
        st.subheader("주문 상태")

        status_rows = pd.DataFrame([
            {
                "상태": item["key"],
                "건수": item["doc_count"]
            }
            for item in summary["status_count"]
        ])

        if not status_rows.empty:
            st.bar_chart(
                status_rows.set_index("상태"),
                height=260
            )

    with lower_right:
        st.subheader("담당자별 매출")

        if not orders_df.empty:
            salesperson = (
                orders_df
                .groupby("salesperson")["revenue"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(
                salesperson,
                height=260
            )

    st.subheader("최근 주문")

    if not orders_df.empty:
        columns = [
            "order_date",
            "order_id",
            "salesperson",
            "customer_type",
            "product",
            "quantity",
            "revenue",
            "status",
        ]

        st.dataframe(
            orders_df
            .sort_values("order_date", ascending=False)
            [columns]
            .head(15),
            use_container_width=True,
            hide_index=True
        )


with tab2:
    question = st.text_area(
        "분석 질문",
        value=(
            f"{region} 지역의 시장 특성과 실제 매출을 비교하고 "
            "영업 인사이트를 알려줘"
        ),
        height=95
    )

    if st.button(
        "AI 분석 실행",
        type="primary"
    ):
        with st.spinner(
            "FAISS 문서 검색과 OpenSearch 매출 분석 중..."
        ):
            rag_docs = search_faiss(
                openai_client,
                question,
                k=top_k
            )

            answer = hybrid_answer(
                openai_client,
                question,
                rag_docs,
                summary
            )

        st.subheader("Executive Brief")
        st.markdown(answer)

        st.subheader("검색 근거")

        st.dataframe(
            [
                {
                    "순위": doc["rank"],
                    "문서": doc["title"].replace("## ", ""),
                    "유사도": round(doc["score"], 4)
                }
                for doc in rag_docs
            ],
            use_container_width=True,
            hide_index=True
        )


with tab3:
    evidence_question = st.text_input(
        "검색 근거 확인용 질문",
        value=f"{region} 지역의 시장 특성"
    )

    if st.button("근거 검색"):
        rag_docs = search_faiss(
            openai_client,
            evidence_question,
            k=top_k
        )

        st.dataframe(
            [
                {
                    "순위": doc["rank"],
                    "문서": doc["title"].replace("## ", ""),
                    "유사도": round(doc["score"], 4)
                }
                for doc in rag_docs
            ],
            use_container_width=True,
            hide_index=True
        )

        with st.expander("검색 문서 원문 보기"):
            for doc in rag_docs:
                st.markdown(
                    f'### {doc["rank"]}위 · '
                    f'{doc["title"].replace("## ", "")}'
                )
                st.text(doc["content"])
                st.divider()
