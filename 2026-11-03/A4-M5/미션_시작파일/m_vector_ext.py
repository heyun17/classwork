# A4-M5 08탭 · 필터와 Hybrid — 실습 폴더로 복사해 python m_vector_ext.py
from clients import get_openai_client, get_opensearch_client
from config import RAG_INDEX, EMBEDDING_MODEL

ai, c = get_openai_client(), get_opensearch_client()

def embed(q):
    return ai.embeddings.create(model=EMBEDDING_MODEL, input=q).data[0].embedding

def knn_filtered(q, k=3, titles=None):
    knn = {"vector": embed(q), "k": k}
    if titles:
        knn["filter"] = {"terms": {"title": titles}}       # A4-M2 03탭 terms
    hits = c.search(index=RAG_INDEX, body={"size": k, "_source": ["title"],
                    "query": {"knn": {"embedding": knn}}})["hits"]["hits"]
    return [(round(h["_score"], 4), h["_source"]["title"]) for h in hits]

q = "공공기관 수요가 많은 곳은?"
print("전체:        ", knn_filtered(q))
print("요약 섹션 제외:", knn_filtered(q, titles=["서울 지역 현황", "부산 지역 현황", "대구 지역 현황",
                                              "대전 지역 현황", "광주 지역 현황"]))

c.transport.perform_request("PUT", "/_search/pipeline/hybrid-pipe", body={
    "phase_results_processors": [{"normalization-processor": {
        "normalization": {"technique": "min_max"},
        "combination": {"technique": "arithmetic_mean", "parameters": {"weights": [0.3, 0.7]}},
    }}]})

def hybrid(q, k=3):
    body = {"size": k, "_source": ["title"], "query": {"hybrid": {"queries": [
        {"match": {"content": q}},                                  # 키워드 (content는 text)
        {"knn": {"embedding": {"vector": embed(q), "k": k}}},       # 벡터
    ]}}}
    hits = c.search(index=RAG_INDEX, body=body, params={"search_pipeline": "hybrid-pipe"})["hits"]["hits"]
    return [(round(h["_score"], 4), h["_source"]["title"]) for h in hits]

for q in ["프로젝터", "인구 940만 명인 곳"]:
    print(q, "| 벡터:", knn_filtered(q), "| Hybrid:", hybrid(q))