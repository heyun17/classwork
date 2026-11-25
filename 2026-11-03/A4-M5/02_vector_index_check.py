from clients import get_opensearch_client
from config import RAG_INDEX
c=get_opensearch_client()
print("문서 수:",c.count(index=RAG_INDEX)["count"])
print(c.indices.get_mapping(index=RAG_INDEX))
r=c.search(index=RAG_INDEX,body={"size":1,"_source":["title","embedding"],"query":{"match_all":{}}})
d=r["hits"]["hits"][0]["_source"]
print("title:",d["title"])
print("embedding 차원:",len(d["embedding"]))
print("앞 10개:",d["embedding"][:10])
