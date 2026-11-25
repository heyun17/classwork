# A4-M5 미션 4 · region 필드를 넣어 rag_docs_v2로 다시 옮기기 — 빈칸(____) 채우기
from clients import get_openai_client, get_opensearch_client
from vector_service import load_existing_faiss
from config import EMBEDDING_MODEL

INDEX = "rag_docs_v2"
c, ai = get_opensearch_client(), get_openai_client()
index, chunks = load_existing_faiss()

if c.indices.exists(index=INDEX):
    c.indices.delete(index=INDEX)
c.indices.create(index=INDEX, body={"settings": {"index": {"knn": True}}, "mappings": {"properties": {
    "title": {"type": "keyword"}, "region": {"type": "keyword"}, "content": {"type": "text"},
    "embedding": {"type": "knn_vector", "dimension": index.d,
                  "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "faiss"}}}}})

for i, chunk in enumerate(chunks):
    title = chunk.splitlines()[0].replace("## ", "")
    region = ______________________________          # "광주 지역 현황" → "광주", 그 외 → "전체"
    c.index(index=INDEX, id=i, body={"title": title, "region": region, "content": chunk,
                                     "embedding": index.reconstruct(i).tolist()})
c.indices.refresh(index=INDEX)

v = ai.embeddings.create(model=EMBEDDING_MODEL, input="주요 수요 제품은?").data[0].embedding
for reg in [None, "광주"]:
    knn = {"vector": v, "k": 3}
    if reg:
        knn["filter"] = {"term": {"region": reg}}
    hits = c.search(index=INDEX, body={"size": 3, "_source": ["title", "region"],
                    "query": {"knn": {"embedding": knn}}})["hits"]["hits"]
    print(reg or "필터 없음", [(h["_source"]["region"], h["_source"]["title"]) for h in hits])