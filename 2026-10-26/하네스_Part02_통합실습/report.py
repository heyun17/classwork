"""시작 코드. 기본 보고서는 구현되지만 min_total 기능은 아직 없다."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent

def make_report(source: Path, destination: Path) -> int:
    """기본 주문 보고서를 생성한다. 추가 필터 기능은 Codex 실습 과제."""
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
        result.append({**row, "total_amount": qty * price})
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
