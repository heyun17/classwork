# ====================================================================
# 파일 용도: OpenSearch 집계 결과와 FAISS 검색 결과를 GPT-4.1-nano에 전달해 답변을 생성합니다.
# ====================================================================

import json

from config import GPT_MODEL

def explain_sales(
    openai_client,
    summary,
    question
):
    response = openai_client.responses.create(
        model=GPT_MODEL,
        max_output_tokens=500,
        input=f"""
다음은 OpenSearch가 직접 계산한 매출 집계입니다.

{json.dumps(summary, ensure_ascii=False)}

질문:
{question}

규칙:
1. 위 집계값만 근거로 답하세요.
2. 숫자를 추측하지 마세요.
3. 금액은 천 단위 쉼표와 원으로 표시하세요.
"""
    )

    return response.output_text

def hybrid_answer(
    openai_client,
    question,
    rag_docs,
    sales_summary
):
    context = "\n\n".join(
        doc["content"]
        for doc in rag_docs
    )

    response = openai_client.responses.create(
        model=GPT_MODEL,
        max_output_tokens=600,
        input=f"""
[FAISS 내부 문서]
{context}

[OpenSearch 실제 매출]
{json.dumps(sales_summary, ensure_ascii=False)}

[사용자 질문]
{question}

규칙:
1. FAISS 문서는 지역·시장·고객 특성의 근거입니다.
2. OpenSearch는 실제 주문·매출·판매수량의 근거입니다.
3. 두 자료를 함께 비교하세요.
4. 제공되지 않은 숫자는 만들지 마세요.
5. 마지막에 업무 인사이트를 간단히 제시하세요.
"""
    )

    return response.output_text
