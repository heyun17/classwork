import unittest
from pathlib import Path
from tools.order_lookup import lookup_order
from tools.contract_check import verify_report
from report import BASE, make_report
import tempfile

class ToolTests(unittest.TestCase):
    def test_lookup_success(self):
        x=lookup_order("O101")
        self.assertTrue(x["ok"])
        self.assertEqual(x["quantity"],2)
    def test_lookup_not_found(self):
        self.assertEqual(lookup_order("O999")["error"],"not_found")
    def test_lookup_input_rejected(self):
        self.assertEqual(lookup_order("invalid")["error"],"invalid_order_id")
    def test_contract_reject_wrong_report(self):
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/"wrong.csv"
            make_report(BASE / "orders.csv", dst)
            result=verify_report(dst,5000)
            self.assertFalse(result["ok"])

if __name__ == "__main__": unittest.main()
