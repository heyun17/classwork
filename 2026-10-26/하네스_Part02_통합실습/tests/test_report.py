"""변경 전에는 신규 기능 테스트만 실패해야 한다."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from report import BASE, make_report

class ReportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = json.loads((BASE / "data/expected.json").read_text(encoding="utf-8"))

    def get_output(self, **kwargs):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "report.csv"
            n = make_report(BASE / "orders.csv", dst, **kwargs)
            with dst.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        return n,rows

    def test_01_base_count_total(self):
        n,rows = self.get_output()
        self.assertEqual(n,self.expected["base_count"])
        self.assertEqual(sum(int(r["total_amount"]) for r in rows),self.expected["base_total"])

    def test_02_original_hash(self):
        actual = hashlib.sha256((BASE / "orders.csv").read_bytes()).hexdigest()
        self.assertEqual(actual,(BASE / "data/source.sha256").read_text().strip())

    def test_03_filter_min_5000(self):
        n,rows = self.get_output(min_total=5000)
        self.assertEqual(n,2)
        self.assertEqual([r["order_id"] for r in rows],["O101","O103"])
        self.assertEqual(sum(int(r["total_amount"]) for r in rows),11000)

    def test_04_zero_min_matches_base(self):
        n,rows = self.get_output(min_total=0)
        self.assertEqual(n,4)

    def test_05_reject_negative_filter(self):
        with self.assertRaises(ValueError):
            self.get_output(min_total=-1)

    def test_06_reject_bad_quantity(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "bad.csv"
            src.write_text("order_id,product,quantity,unit_price\nO1,노트,-1,3000\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                make_report(src,Path(td) / "out.csv")

if __name__ == "__main__":unittest.main()
