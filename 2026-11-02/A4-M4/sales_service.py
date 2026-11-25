# ====================================================================
# 파일 용도: OpenSearch sales 인덱스의 조회·집계 기능을 공통 함수로 제공합니다.
# 참고용으로 CSV 업로드 함수도 포함하지만 Part 1 필수 실습에서는 사용하지 않습니다.
# ====================================================================

import pandas as pd
from opensearchpy.helpers import bulk

from config import CSV_PATH, SALES_INDEX

MAPPING = {
    "mappings": {
        "properties": {
            "order_id": {"type": "keyword"},
            "order_date": {"type": "date"},
            "region": {"type": "keyword"},
            "sales_team": {"type": "keyword"},
            "salesperson": {"type": "keyword"},
            "customer_type": {"type": "keyword"},
            "category": {"type": "keyword"},
            "product": {"type": "keyword"},
            "quantity": {"type": "integer"},
            "unit_price": {"type": "integer"},
            "discount_rate": {"type": "integer"},
            "revenue": {"type": "long"},
            "satisfaction": {"type": "integer"},
            "status": {"type": "keyword"}
        }
    }
}


def read_sales_csv():
    """제공된 CSV 원본을 pandas DataFrame으로 읽습니다."""
    return pd.read_csv(CSV_PATH)


def create_sales_index_if_needed(os_client):
    """sales 인덱스가 없을 때만 Mapping과 함께 생성합니다."""
    if os_client.indices.exists(index=SALES_INDEX):
        return False

    os_client.indices.create(
        index=SALES_INDEX,
        body=MAPPING
    )
    return True


def upload_sales_dataframe(os_client, df):
    """참고용: DataFrame의 각 행을 OpenSearch 문서로 Bulk 업로드합니다."""
    actions = []

    for row in df.to_dict(orient="records"):
        actions.append({
            "_index": SALES_INDEX,
            "_id": row["order_id"],
            "_source": row
        })

    success, errors = bulk(
        os_client,
        actions,
        raise_on_error=False
    )

    os_client.indices.refresh(index=SALES_INDEX)
    return success, errors


def get_regions(os_client):
    """OpenSearch sales 인덱스에 실제 존재하는 지역 목록을 반환합니다."""
    result = os_client.search(
        index=SALES_INDEX,
        body={
            "size": 0,
            "aggs": {
                "regions": {
                    "terms": {
                        "field": "region",
                        "size": 100
                    }
                }
            }
        }
    )

    return [
        bucket["key"]
        for bucket in result["aggregations"]["regions"]["buckets"]
    ]


def get_region_summary(os_client, region="서울"):
    """선택 지역의 KPI와 제품/상태 집계를 반환합니다."""
    result = os_client.search(
        index=SALES_INDEX,
        body={
            "size": 0,
            "query": {
                "term": {
                    "region": region
                }
            },
            "aggs": {
                "total_revenue": {
                    "sum": {"field": "revenue"}
                },
                "avg_revenue": {
                    "avg": {"field": "revenue"}
                },
                "total_quantity": {
                    "sum": {"field": "quantity"}
                },
                "avg_satisfaction": {
                    "avg": {"field": "satisfaction"}
                },
                "status_count": {
                    "terms": {
                        "field": "status",
                        "size": 10
                    }
                },
                "product_sales": {
                    "terms": {
                        "field": "product",
                        "size": 20,
                        "order": {"sales": "desc"}
                    },
                    "aggs": {
                        "sales": {
                            "sum": {"field": "revenue"}
                        }
                    }
                }
            }
        }
    )

    return {
        "region": region,
        "order_count": result["hits"]["total"]["value"],
        "total_revenue": result["aggregations"]["total_revenue"]["value"],
        "avg_revenue": result["aggregations"]["avg_revenue"]["value"],
        "total_quantity": result["aggregations"]["total_quantity"]["value"],
        "avg_satisfaction": result["aggregations"]["avg_satisfaction"]["value"],
        "status_count": result["aggregations"]["status_count"]["buckets"],
        "product_sales": result["aggregations"]["product_sales"]["buckets"],
    }


def get_region_documents(os_client, region="서울", size=1000):
    """Streamlit 차트용으로 선택 지역의 실제 주문 문서를 DataFrame으로 반환합니다."""
    result = os_client.search(
        index=SALES_INDEX,
        body={
            "size": size,
            "query": {
                "term": {
                    "region": region
                }
            },
            "sort": [
                {"order_date": {"order": "asc"}}
            ]
        }
    )

    rows = [
        hit["_source"]
        for hit in result["hits"]["hits"]
    ]

    df = pd.DataFrame(rows)

    if not df.empty:
        df["order_date"] = pd.to_datetime(df["order_date"])

    return df
