"""외부 시스템 연결 전 로컬 읽기 전용 Tool Contract 실습."""
import csv
import json
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "orders.csv"

def lookup_order(order_id: str) -> dict:
    """order_id를 입력받아 결과 JSON만 반환. 쓰기·삭제 작업 없음."""
    if not isinstance(order_id,str) or not order_id.startswith("O"):
        return {"ok":False,"error":"invalid_order_id","order_id":str(order_id)}
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:
        row=next((r for r in csv.DictReader(f) if r["order_id"] == order_id),None)
    if row is None:
        return {"ok":False,"error":"not_found","order_id":order_id}
    return {"ok":True,"order_id":order_id,"product":row["product"],
            "quantity":int(row["quantity"]),"unit_price":int(row["unit_price"])}

if __name__ == "__main__":
    print(json.dumps(lookup_order(sys.argv[1] if len(sys.argv)>1 else ""),ensure_ascii=False))
