from config import SALES_INDEX

def get_region_summary(os_client, region):
    result = os_client.search(
        index=SALES_INDEX,
        body={
            "size": 0,
            "query": {"term": {"region": region}},
            "aggs": {
                "total_revenue": {"sum": {"field": "revenue"}},
                "avg_revenue": {"avg": {"field": "revenue"}},
                "total_quantity": {"sum": {"field": "quantity"}},
                "avg_satisfaction": {"avg": {"field": "satisfaction"}},
                "product_sales": {
                    "terms": {
                        "field": "product",
                        "size": 10,
                        "order": {"sales": "desc"}
                    },
                    "aggs": {"sales": {"sum": {"field": "revenue"}}}
                }
            }
        }
    )
    a = result["aggregations"]
    return {
        "region": region,
        "order_count": result["hits"]["total"]["value"],
        "total_revenue": a["total_revenue"]["value"],
        "avg_revenue": a["avg_revenue"]["value"],
        "total_quantity": a["total_quantity"]["value"],
        "avg_satisfaction": a["avg_satisfaction"]["value"],
        "product_sales": a["product_sales"]["buckets"]
    }
