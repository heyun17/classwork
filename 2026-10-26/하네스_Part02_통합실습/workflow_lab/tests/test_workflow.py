"""python -m unittest discover -s workflow_lab/tests -v"""
import unittest
from workflow_lab.runner import run_case


class WorkflowTests(unittest.TestCase):
    def test_success_runs_both_reviews(self):
        r = run_case("pass")
        self.assertEqual(r["decision"], "PASS")
        self.assertEqual(r["stages"]["schema_review"], "PASS")
        self.assertEqual(r["stages"]["source_review"], "PASS")
        self.assertFalse(r["released"])  # 모의 게이트, 실제 배포 없음

    def test_bad_contract_skips_reviews(self):
        r = run_case("false_success_claim")
        self.assertEqual(r["stages"]["contract_gate"], "BLOCK")
        self.assertEqual(r["stages"]["schema_review"], "SKIP")
        self.assertEqual(r["stages"]["source_review"], "SKIP")
        self.assertEqual(r["stages"]["release_gate"], "SKIP")

    def test_missing_artifact_skips(self):
        self.assertEqual(run_case("missing_file")["stages"]["schema_review"], "SKIP")

    def test_bad_request_stops_first(self):
        r = run_case("bad_request")
        self.assertEqual(r["stages"]["intake"], "BLOCK")
        self.assertEqual(r["stages"]["contract_gate"], "SKIP")

    def test_transient_retry_is_bounded(self):
        r = run_case("pass", "temporary")
        self.assertEqual(r["decision"], "PASS")
        self.assertEqual(r["audits"]["source_review"]["attempts"], 2)

    def test_persistent_failure_blocks_gate(self):
        r = run_case("pass", "persistent")
        self.assertEqual(r["decision"], "BLOCK")
        self.assertEqual(r["audits"]["source_review"]["attempts"], 2)
        self.assertEqual(r["stages"]["release_gate"], "BLOCK")

    def test_invalid_contract_does_not_retry(self):
        r = run_case("pass", "invalid")
        self.assertEqual(r["decision"], "BLOCK")
        self.assertEqual(r["audits"]["source_review"]["attempts"], 1)

    def test_false_claim_and_offset_error_both_block(self):
        self.assertEqual(run_case("offsetting_row_errors")["decision"], "BLOCK")
        self.assertEqual(run_case("fake_summary")["decision"], "BLOCK")

    def test_no_publish_side_effect_even_if_success(self):
        self.assertIs(run_case("pass")["released"], False)

    def test_unknown_case_is_explicit(self):
        with self.assertRaises(ValueError):
            run_case("no-such-case")


if __name__ == "__main__":
    unittest.main()
