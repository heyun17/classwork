"""안전한 실패 재현: 임시 디렉터리의 복사본만 수정한다."""
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import hashlib

BASE = Path(__file__).resolve().parents[1]

def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    real_source = BASE / "starter" / "orders.csv"
    real_before = sha(real_source)
    with TemporaryDirectory() as d:
        temp = Path(d)
        source = temp / "orders.csv"
        source.write_bytes(real_source.read_bytes())
        before = sha(source)
        with source.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        total = 0
        for row in rows:
            row["total_amount"] = str(int(row["quantity"]) * int(row["unit_price"]))
            total += int(row["total_amount"])
        report = temp / "report.csv"
        # 잘못된 구현: 리포트 파일을 만들면서 원본에도 새 열을 덮어쓴다.
        for target in (report, source):
            with target.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        after = sha(source)
        print(f"보고서 행: {len(rows)} / 총액: {total}")
        print(f"임시 원본 해시 일치: {before == after}")
        print(f"실제 starter 원본 유지: {sha(real_source) == real_before}")
        print("결론: 보고서 금액이 맞아도 원본 파일 변경은 실패")

if __name__ == "__main__": run()
