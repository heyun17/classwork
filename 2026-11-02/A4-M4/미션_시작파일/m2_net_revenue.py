# A4-M4 미션 2 · 취소 주문을 뺀 매출 — 빈칸(____)을 채워 실행
# 실행: 이 파일을 실습 폴더(config.py가 있는 곳)로 복사한 뒤 python m2_net_revenue.py
from clients import get_opensearch_client
from config import SALES_INDEX

def get_net_revenue(os_client, region):
    result = os_client.search(index=SALES_INDEX, body={
        "size": 0,
        "query": {"bool": {
            "filter":   [{"term": {"region": region}}],
            "must_not": [____________________________],
        }},
        "aggs": {"net_revenue": {"sum": {"field": "revenue"}}},
    })
    return result["aggregations"]["net_revenue"]["value"]

os_client = get_opensearch_client()
for r in ["서울", "광주"]:
    print(r, f"{get_net_revenue(os_client, r):,.0f}원")
# 정답: 서울 58,083,000원 / 광주 34,921,500원
