import json
from config import GPT_MODEL
from vector_service import knn_search
from sales_service import get_region_summary

def run_vector_rag(openai_client, os_client, question, region, k=3):
    hits = knn_search(openai_client, os_client, question, k)
    context = "\n\n".join(hit["_source"]["content"] for hit in hits)
    sales = get_region_summary(os_client, region)

    response = openai_client.responses.create(
        model=GPT_MODEL,
        max_output_tokens=500,
        input=f"""[OpenSearch Vector 검색 문서]
{context}

[OpenSearch sales 집계]
{json.dumps(sales, ensure_ascii=False)}

[질문]
{question}

제공된 자료에 근거해서만 답하세요.
숫자를 임의로 만들지 마세요."""
    )
    return response.output_text, hits, sales
