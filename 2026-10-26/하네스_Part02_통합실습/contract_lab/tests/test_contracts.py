import json
import unittest
from pathlib import Path
from contract_lab.contracts import validate_request, verify_delivery
P=Path(__file__).resolve().parents[1]/'fixtures'
request=json.loads((P/'request_ok.json').read_text(encoding='utf8'))
cases=json.loads((P/'candidates.json').read_text(encoding='utf8'))
class ContractTests(unittest.TestCase):
    def test_ok(self):self.assertEqual(verify_delivery(request,cases['pass'])['decision'],'PASS')
    def test_lie_about_success(self):self.assertEqual(verify_delivery(request,cases['false_success_claim'])['decision'],'BLOCK')
    def test_missing_id(self):self.assertEqual(verify_delivery(request,cases['missing_id'])['decision'],'BLOCK')
    def test_missing_file(self):self.assertEqual(verify_delivery(request,cases['missing_file'])['decision'],'BLOCK')
    def test_wrong_request(self):self.assertIn('REQUEST_ID_MISMATCH',verify_delivery(request,cases['wrong_request_id'])['issues'])
    def test_escape(self):self.assertIn('ARTIFACT_INVALID_OR_MISSING',verify_delivery(request,cases['path_escape'])['issues'])
    def test_fake_summary(self):self.assertIn('DECLARATION_MISMATCH',verify_delivery(request,cases['fake_summary'])['issues'])
    def test_missing_field(self):self.assertIn('RESPONSE_SCHEMA_INVALID',verify_delivery(request,cases['missing_field'])['issues'])
    def test_bool_as_minimum(self):self.assertIn('THRESHOLD_INVALID',validate_request({**request,'min_total':True}))
    def test_negative_minimum(self):self.assertIn('THRESHOLD_INVALID',validate_request({**request,'min_total':-1}))
    def test_source_path_rejected(self):self.assertIn('SOURCE_NOT_ALLOWED',validate_request({**request,'source_file':'../orders.csv'}))
    def test_response_check_report(self):
        result=verify_delivery(request,cases['pass'])
        self.assertTrue(all(result['checks'].values()))
if __name__=='__main__':unittest.main()

class RegressionCases(unittest.TestCase):
    """초기 교안 검증기에서 놓쳤던 거짓 합격 사례를 회귀 테스트로 고정."""
    def test_changed_threshold_is_not_wrongly_accepted(self):
        self.assertEqual(verify_delivery({**request,'min_total':10000},cases['pass'])['decision'],'BLOCK')
    def test_valid_alternative_threshold_can_pass(self):
        # 같은 원본에서 6000 이상인 주문은 O101 한 건뿐이다.
        fixed={**cases['pass'],'artifact_path':'contract_lab/fixtures/filtered_6000.csv',
               'declared_count':1,'declared_total':6000}
        self.assertEqual(verify_delivery({**request,'min_total':6000},fixed)['decision'],'PASS')
    def test_balanced_wrong_rows_are_blocked(self):
        bad={**cases['pass'],'artifact_path':'contract_lab/fixtures/filtered_offset.csv'}
        result=verify_delivery(request,bad)
        self.assertEqual(result['decision'],'BLOCK')
        self.assertIn('ROW_VALUES_MISMATCH',result['issues'])
        self.assertIn('ROW_TOTAL_MISMATCH',result['issues'])
        self.assertNotIn('TOTAL_MISMATCH',result['issues'])
    def test_list_request_is_blocked_instead_of_crashing(self):
        self.assertIn('REQUEST_NOT_OBJECT',verify_delivery(['invalid'],cases['pass'])['issues'])
    def test_bool_success_claim_is_required(self):
        self.assertIn('CANDIDATE_NOT_COMPLETED',verify_delivery(request,{**cases['pass'],'ok':False})['issues'])
    def test_duplicate_rows_are_rejected(self):
        result=verify_delivery(request,{**cases['pass'],'artifact_path':'contract_lab/fixtures/filtered_duplicate.csv'})
        self.assertTrue(any('DUPLICATE_ORDER_ID' in x for x in result['issues']))
    def test_extra_request_field_is_rejected(self):
        self.assertIn('REQUEST_FIELDS_INVALID',validate_request({**request,'currency':'KRW'}))
    def test_invalid_response_is_blocked(self):
        self.assertIn('RESPONSE_NOT_OBJECT',verify_delivery(request,'done')['issues'])
