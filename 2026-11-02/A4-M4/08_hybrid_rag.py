# ====================================================================
# 파일 용도: FAISS 내부문서 검색과 OpenSearch 실제 매출 집계를 결합한 통합 RAG를 실행합니다.
# ====================================================================

from clients import (
    get_openai_client,
    get_opensearch_client,
)
from faiss_service import search_faiss
from sales_service import get_region_summary
from rag_service import hybrid_answer

openai_client = get_openai_client()
os_client = get_opensearch_client()

question = (
    "광주 지역의 시장 특성과 "
    "실제 매출을 비교해줘"
)

rag_docs = search_faiss(
    openai_client,
    question,
    k=3
)

sales_summary = get_region_summary(
    os_client,
    region="광주"
)

answer = hybrid_answer(
    openai_client,
    question,
    rag_docs,
    sales_summary
)

print(answer)
