# ====================================================================
# 파일 용도: OpenSearch sales 인덱스의 지역별 매출·수량·만족도·제품별 매출을 집계합니다.
# ====================================================================

import json

from clients import get_opensearch_client
from sales_service import get_region_summary

os_client = get_opensearch_client()

summary = get_region_summary(
    os_client,
    region="서울"
)

print(
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2
    )
)
