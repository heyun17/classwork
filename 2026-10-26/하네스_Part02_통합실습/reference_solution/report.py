"""비교 확인용 정답 예제. 실습 전 starter에 복사하지 않는다."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent

def make_report(source: Path, destination: Path, *, min_total: int = 0) -> int:
    if min_total < 0:
        raise ValueError("min_total은 0 이상이어야 합니다")
    with Path(source).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("주문 데이터가 없습니다")
    seen = set()
    result = []
    for row in rows:
        order_id = row["order_id"]
        if order_id in seen:
            raise ValueError("중복 주문 ID")
        seen.add(order_id)
        qty = int(row["quantity"])
        price = int(row["unit_price"])
        if qty < 0 or price < 0:
            raise ValueError("음수 수량·단가")
        total = qty * price
        if total >= min_total:
            result.append({**row, "total_amount": total})
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[*rows[0].keys(), "total_amount"])
        writer.writeheader()
        writer.writerows(result)
    return len(result)

if __name__ == "__main__":
    n = make_report(BASE / "orders.csv", BASE / "output" / "report.csv")
    print(f"생성: {n}건 / output/report.csv")
