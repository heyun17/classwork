"""Codex가 완성할 주문 보고서: 시작 파일에는 기능이 구현되어 있지 않다."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent

REQUIRED_COLUMNS = ("order_id", "product", "quantity", "unit_price")


def make_report(source: Path, destination: Path, min_total: int = 0) -> int:
    """원본 CSV를 변경하지 않고 주문 금액 보고서를 생성한다."""
    source = Path(source)
    destination = Path(destination)
    rows = []
    seen_order_ids = set()

    with source.open(encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if reader.fieldnames is None or any(
            column not in reader.fieldnames for column in REQUIRED_COLUMNS
        ):
            raise ValueError("필수 열이 누락되었습니다.")

        for line_number, row in enumerate(reader, start=2):
            order_id = row["order_id"]
            if order_id in seen_order_ids:
                raise ValueError(f"중복 주문 ID: {order_id}")
            seen_order_ids.add(order_id)

            try:
                quantity = int(row["quantity"])
                unit_price = int(row["unit_price"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{line_number}행의 수량과 단가는 정수여야 합니다."
                ) from exc

            if quantity < 0:
                raise ValueError(f"음수 수량은 허용되지 않습니다: {order_id}")

            total_amount = quantity * unit_price
            if total_amount >= min_total:
                output_row = dict(row)
                output_row["total_amount"] = str(total_amount)
                rows.append(output_row)

    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*reader.fieldnames, "total_amount"]
    with destination.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    count = make_report(BASE / "orders.csv", BASE / "output" / "report.csv")
    print(f"보고서 {count}건 생성: output/report.csv")
