# A4-M5 미션 5 · 04를 run_vector_rag로
from clients import get_openai_client, get_opensearch_client
from rag_service import run_vector_rag

answer, hits, sales = run_vector_rag(get_openai_client(), get_opensearch_client(),
                                     "광주 지역의 시장 특성과 실제 매출을 비교해줘", region="광주", k=3)
print([h["_source"]["title"] for h in hits])
print([(p["key"], p["sales"]["value"]) for p in sales["product_sales"]][:3])
print(answer)