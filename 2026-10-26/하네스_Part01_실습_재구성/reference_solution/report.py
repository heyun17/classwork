"""작업 결과 비교용 모범 구현. 사전 비교 실행에는 사용하지 않는다."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent

def make_report(source: Path, destination: Path, min_total: int = 0) -> int:
    if min_total < 0:
        raise ValueError("최소 금액은 음수일 수 없습니다")
    with source.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("주문 데이터가 비었습니다")
    seen, result = set(), []
    for row in rows:
        order_id = row["order_id"].strip()
        if not order_id or order_id in seen:
            raise ValueError("주문 ID가 비었거나 중복되었습니다")
        seen.add(order_id)
        quantity, price = int(row["quantity"]), int(row["unit_price"])
        if quantity <= 0 or price < 0:
            raise ValueError("수량·단가가 유효하지 않습니다")
        amount = quantity * price
        if amount >= min_total:
            result.append({"order_id": order_id, "product": row["product"],
                           "quantity": quantity, "unit_price": price,
                           "total_amount": amount})
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = ["order_id", "product", "quantity", "unit_price", "total_amount"]
    with destination.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    return len(result)

if __name__ == "__main__":
    count = make_report(BASE / "orders.csv", BASE / "output" / "report.csv")
    print(f"보고서 {count}건 생성: output/report.csv")
