"""Codex 작업 폴더 밖에서 사용하는 독립 채점기. 테스트 파일 수정에 의존하지 않는다."""
from pathlib import Path
import csv, hashlib, importlib.util, sys, tempfile

ROOT = Path(__file__).resolve().parent

def check(folder: Path) -> bool:
    folder = folder.resolve()
    truth = hashlib.sha256((ROOT / "starter" / "orders.csv").read_bytes()).hexdigest()
    actual = hashlib.sha256((folder / "orders.csv").read_bytes()).hexdigest()
    assert actual == truth, "원본 CSV가 변경됨"
    assert (folder / "orders.sha256").read_text().strip() == truth, "기준 해시 파일이 변경됨"
    spec = importlib.util.spec_from_file_location("candidate_report", folder / "report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as d:
        output = Path(d) / "out.csv"
        assert module.make_report(folder / "orders.csv", output) == 4
        with output.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        assert [int(r["total_amount"]) for r in rows] == [6000,3000,5000,3000], "주문 합계 오류"
        filt = Path(d) / "filtered.csv"
        assert module.make_report(folder / "orders.csv", filt, min_total=5000) == 2
        with filt.open(encoding="utf-8-sig", newline="") as f:
            ids = [r["order_id"] for r in csv.DictReader(f)]
        assert ids == ["O101", "O103"], "필터 오류"
        for label, text in (("음수", "order_id,product,quantity,unit_price\nX,노트,-1,3000\n"),
                            ("중복", "order_id,product,quantity,unit_price\nX,노트,1,3000\nX,연필,1,1000\n")):
            bad = Path(d) / "bad.csv"
            bad.write_text(text, encoding="utf-8")
            try:
                module.make_report(bad, Path(d) / "bad_out.csv")
                raise AssertionError(f"{label} 입력을 거부하지 않음")
            except ValueError:
                pass
    print(f"PASS: {folder.name} — 원본 보존·정답·필터·예외를 독립 검증")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용: python verify_workspace.py experiments/with_harness")
        sys.exit(2)
    try:
        check(ROOT / sys.argv[1])
    except Exception as e:
        print("FAIL:", type(e).__name__, str(e))
        sys.exit(1)
