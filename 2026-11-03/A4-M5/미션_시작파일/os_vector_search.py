# A4-M5 미션 6 · A4-M4 폴더로 복사해서 사용 (m6_app.py가 import)
from config import EMBEDDING_MODEL
RAG_INDEX = "rag_docs"

def count_docs(os_client):
    return os_client.count(index=RAG_INDEX)["count"]

def search_opensearch(openai_client, os_client, question, k=3):
    v = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=question).data[0].embedding
    hits = os_client.search(index=RAG_INDEX, body={"size": k, "_source": ["title", "content"],
                            "query": {"knn": {"embedding": {"vector": v, "k": k}}}})["hits"]["hits"]
    # app.py가 기대하는 모양(rank, score, title, content)으로 맞춰 돌려줌
    return [{"rank": i + 1, "score": h["_score"], "title": "## " + h["_source"]["title"],
             "content": h["_source"]["content"]} for i, h in enumerate(hits)]