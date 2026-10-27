"""실행 결과가 하네스 계약을 만족하는지 결정적으로 검사."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def verify_report(path: Path, min_total:int)->dict:
    e=json.loads((ROOT / "data/expected.json").read_text(encoding="utf-8"))
    if min_total != e["min_total"]:
        raise ValueError("이 검증 스크립트의 테스트 임계값은 5000입니다")
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    actual_ids=[r["order_id"] for r in rows]
    amount=sum(int(r["total_amount"]) for r in rows)
    sha=hashlib.sha256((ROOT / "orders.csv").read_bytes()).hexdigest()
    digest=(ROOT / "data/source.sha256").read_text().strip()
    checks={"expected_ids":actual_ids==e["filtered_ids"],
            "expected_total":amount==e["filtered_total"],
            "source_unchanged":sha==digest}
    return {"ok":all(checks.values()),"checks":checks,
            "actual_ids":actual_ids,"actual_total":amount}
