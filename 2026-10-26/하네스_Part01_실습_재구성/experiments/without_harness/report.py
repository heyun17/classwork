"""주문 CSV를 검증하고 금액 보고서를 생성한다."""
import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent


def make_report(source: Path, destination: Path, min_total: int = 0) -> int:
    """원본 CSV를 수정하지 않고 주문 금액을 계산해 결과 CSV로 저장한다."""
    source = Path(source)
    destination = Path(destination)
    rows = []
    seen_order_ids = set()

    with source.open(encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        required_fields = {"order_id", "quantity", "unit_price"}
        if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
            raise ValueError("입력 CSV에 필요한 열이 없습니다.")

        for row in reader:
            order_id = row["order_id"]
            if order_id in seen_order_ids:
                raise ValueError(f"중복 주문 ID: {order_id}")
            seen_order_ids.add(order_id)

            try:
                quantity = int(row["quantity"])
                unit_price = int(row["unit_price"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"주문 {order_id}의 수량 또는 단가가 올바르지 않습니다."
                ) from exc

            if quantity < 0:
                raise ValueError(f"주문 {order_id}의 수량은 음수일 수 없습니다.")
            if unit_price < 0:
                raise ValueError(f"주문 {order_id}의 단가는 음수일 수 없습니다.")

            total_amount = quantity * unit_price
            if total_amount >= min_total:
                rows.append({**row, "total_amount": total_amount})

        fieldnames = [*reader.fieldnames, "total_amount"]

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    count = make_report(BASE / "orders.csv", BASE / "output" / "report.csv")
    print(f"보고서 {count}건 생성: output/report.csv")
