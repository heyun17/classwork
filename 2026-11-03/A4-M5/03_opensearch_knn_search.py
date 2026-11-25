from clients import get_openai_client,get_opensearch_client
from vector_service import knn_search
hits=knn_search(get_openai_client(),get_opensearch_client(),"광주 지역의 시장 특성은?",3)
for n,h in enumerate(hits,1):print(n,round(h["_score"],4),h["_source"]["title"])
