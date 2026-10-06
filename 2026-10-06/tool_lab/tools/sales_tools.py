from collections import defaultdict
from tools.loader import load_rows


def summarize_sales(top_n: int = 3) -> dict:
    """전체 매출을 집계하고 지역별 상위 n개를 돌려준다."""
    rows = load_rows()

    by_region = defaultdict(int)

    for r in rows:
        by_region[r["region"]] += r["amount"]

    ranked = sorted(
        by_region.items(),
        key=lambda kv: -kv[1]
    )[:top_n]

    return {
        "count": len(rows),
        "total": sum(r["amount"] for r in rows),
        "by_region": [
            {"name": n, "amount": a}
            for n, a in ranked
        ]
    }

def region_detail(region: str="서울", min_amount: int = 0) -> dict:
    """한 지역의 거래를 돌려준다. min_amount 이상만 포함한다."""
    rows = [r for r in load_rows()
        if r["region"] == region and r["amount"] >= min_amount]
    return {
        "region": region,
        "count": len(rows),
        "total": sum(r["amount"] for r in rows),

        "items": [{"date": r["date"], "product": r["product"],
                   "amount": r["amount"]} for r in rows]}

import inspect
sig = inspect.signature(region_detail)
print(sig)
print(sig.parameters.values())
for p in sig.parameters.values():
    print(p.annotation)