# A4-M4 미션 5 · 질문에서 지역 자동 찾기 — 빈칸(________)을 채워 실행
# 실행: 실습 폴더로 복사한 뒤 python m5_auto_region.py
from clients import get_openai_client, get_opensearch_client
from faiss_service import search_faiss
from sales_service import get_regions, get_region_summary
from rag_service import hybrid_answer

openai_client = get_openai_client()
os_client = get_opensearch_client()

question = "대전 지역의 시장 특성과 실제 매출을 비교해줘"
regions = get_regions(os_client)                     # ['광주', '대구', '서울', ...]
found = [r for r in regions if ________ in question]

if not found:
    print("질문에서 지역을 찾지 못했습니다. 지역명을 넣어 질문해 주세요:", regions)
else:
    region = found[0]
    rag_docs = search_faiss(openai_client, question, k=3)
    summary = get_region_summary(os_client, region=region)
    print("집계 지역:", region)
    print(hybrid_answer(openai_client, question, rag_docs, summary))
# 확인: 집계 지역 대전, 답변의 매출 31,861,500원
