# ====================================================================
# 파일 용도: OpenSearch가 계산한 집계 결과를 GPT-4.1-nano가 자연어로 설명하도록 합니다.
# ====================================================================

from clients import (
    get_openai_client,
    get_opensearch_client,
)
from sales_service import get_region_summary
from rag_service import explain_sales

openai_client = get_openai_client()
os_client = get_opensearch_client()

question = "서울 지역 매출 현황을 알려줘"

summary = get_region_summary(
    os_client,
    region="서울"
)

answer = explain_sales(
    openai_client,
    summary,
    question
)

print(answer)
