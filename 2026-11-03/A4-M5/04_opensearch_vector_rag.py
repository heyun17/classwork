import json
from clients import get_openai_client,get_opensearch_client
from vector_service import knn_search
from config import GPT_MODEL,SALES_INDEX
ai=get_openai_client();c=get_opensearch_client()
q="광주 지역의 시장 특성과 실제 매출을 비교해줘";region="광주"
hits=knn_search(ai,c,q,3)
context="\n\n".join(h["_source"]["content"] for h in hits)
r=c.search(index=SALES_INDEX,body={"size":0,"query":{"term":{"region":region}},"aggs":{"total":{"sum":{"field":"revenue"}},"qty":{"sum":{"field":"quantity"}}}})
sales={"region":region,"orders":r["hits"]["total"]["value"],"revenue":r["aggregations"]["total"]["value"],"quantity":r["aggregations"]["qty"]["value"]}
a=ai.responses.create(model=GPT_MODEL,max_output_tokens=500,input=f"[문서]\n{context}\n[매출]\n{json.dumps(sales,ensure_ascii=False)}\n질문:{q}\n제공 자료만 근거로 답하세요.")
print(a.output_text)
