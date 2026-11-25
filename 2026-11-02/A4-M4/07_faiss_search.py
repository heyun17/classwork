# ====================================================================
# 파일 용도: 저장된 FAISS 객체를 불러와 질문 벡터와 Top-K 유사도 검색을 수행합니다.
# ====================================================================

from clients import get_openai_client
from faiss_service import search_faiss

openai_client = get_openai_client()

question = "광주 지역의 시장 특성은?"

results = search_faiss(
    openai_client,
    question,
    k=3
)

for result in results:
    print(
        result["rank"],
        f'{result["score"]:.4f}',
        result["title"]
    )
