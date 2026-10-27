"""최종 응답을 원본 업무 데이터로 검증한다. LLM·API 지식 불필요."""
import csv
from pathlib import Path
SOURCE = Path(__file__).resolve().parent / "starter" / "orders.csv"

def verify_candidate(candidate: dict, source: Path = SOURCE):
    with source.open(encoding="utf-8-sig", newline="") as f:
        rows = {row["order_id"]: row for row in csv.DictReader(f)}
    key = candidate.get("order_id")
    if key not in rows:
        return False, "BLOCK: 존재하지 않는 주문 ID"
    expected = int(rows[key]["quantity"]) * int(rows[key]["unit_price"])
    amount = candidate.get("total_amount")
    if type(amount) is not int or amount != expected:
        return False, f"BLOCK: 금액 불일치 (정답 {expected})"
    return True, "PASS: 원본과 일치"

if __name__ == "__main__":
    for x in [{"order_id":"O101","total_amount":6000},
              {"order_id":"O999","total_amount":6000},
              {"order_id":"O101","total_amount":9000}]:
        print(x, "→", verify_candidate(x)[1])
