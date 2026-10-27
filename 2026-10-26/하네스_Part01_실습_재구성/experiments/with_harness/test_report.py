"""Codex 실행 전에는 실패하고, 기능 구현 뒤에는 통과해야 하는 검증셋."""
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from report import BASE, make_report

class ContractTests(unittest.TestCase):
    def test_01_expected_values(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.csv"
            count = make_report(BASE / "orders.csv", out)
            with out.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(count, 4)
        self.assertEqual([int(r["total_amount"]) for r in rows], [6000,3000,5000,3000])
        self.assertEqual(sum(int(r["total_amount"]) for r in rows), 17000)

    def test_02_min_total_filter(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.csv"
            count = make_report(BASE / "orders.csv", out, min_total=5000)
            with out.open(encoding="utf-8-sig", newline="") as f:
                ids = [r["order_id"] for r in csv.DictReader(f)]
        self.assertEqual(count, 2)
        self.assertEqual(ids, ["O101", "O103"])

    def test_03_source_unchanged(self):
        expected = (BASE / "orders.sha256").read_text().strip()
        before = hashlib.sha256((BASE / "orders.csv").read_bytes()).hexdigest()
        self.assertEqual(before, expected)
        with tempfile.TemporaryDirectory() as d:
            make_report(BASE / "orders.csv", Path(d) / "out.csv")
        self.assertEqual(hashlib.sha256((BASE / "orders.csv").read_bytes()).hexdigest(), expected)

    def test_04_invalid_quantity(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "bad.csv"
            src.write_text("order_id,product,quantity,unit_price\nO101,노트,-1,3000\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                make_report(src, Path(d) / "out.csv")

    def test_05_duplicate_id(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "bad.csv"
            src.write_text("order_id,product,quantity,unit_price\nO101,노트,1,3000\nO101,연필,1,1000\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                make_report(src, Path(d) / "out.csv")

if __name__ == "__main__": unittest.main()
