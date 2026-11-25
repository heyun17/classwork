# A4-M5 미션 2 · 벡터 길이 확인
import numpy as np
from clients import get_opensearch_client
from config import RAG_INDEX

c = get_opensearch_client()
hits = c.search(index=RAG_INDEX, body={"size": 10, "_source": ["title", "embedding"]})["hits"]["hits"]
for h in hits:
    v = np.array(h["_source"]["embedding"])
    print(h["_source"]["title"], len(v), round(float(np.linalg.norm(v)), 4))