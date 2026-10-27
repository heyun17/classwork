import tempfile
import unittest
from pathlib import Path
from checker import BASE, load_rules, scan
from tree_lookup import find_rule, load_tree

class ProjectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(BASE/'rules.csv')
        cls.html = (BASE/'sample.html').read_text(encoding='utf8')
        cls.out = {(r['target'],r['rule_id']):r['outcome'] for r in scan(cls.html, cls.rules)}
    def test_applied_only(self):
        self.assertEqual(len(self.rules), 7)
        self.assertNotIn('COMP-LINK-003',{r.rule_id for r in self.rules})
    def test_standard_and_company_diverge(self):
        self.assertEqual(self.out['L02','LINK-002'],'cantTell')
        self.assertEqual(self.out['L02','COMP-LINK-001'],'failed')
    def test_alt_empty_passes_attribute_test(self):
        self.assertEqual(self.out['I01','IMG-001'],'failed')
        self.assertEqual(self.out['I02','IMG-001'],'passed')
    def test_form_policy(self):
        self.assertEqual(self.out['F03','FORM-001'],'passed')
        self.assertEqual(self.out['F03','COMP-FORM-001'],'failed')
    def test_tree_uses_file_and_rule_id(self):
        node, rule=find_rule('N_COMP_LINK_001')
        self.assertEqual(node['file'],'rules.csv')
        self.assertEqual(rule['rule_id'],'COMP-LINK-001')
    def test_tree_parent_integrity(self):
        nodes, by_id=load_tree()
        self.assertEqual(len(nodes),16)
        self.assertIn('ROOT',by_id)
    def test_draft_not_applied(self):
        all_rules=load_rules(BASE/'rules.csv',active_only=False)
        self.assertEqual(len(all_rules),8)
        self.assertEqual(next(r.status for r in all_rules if r.rule_id=='COMP-LINK-003'),'proposed')
    def test_bad_rule_operator(self):
        raw=(BASE/'rules.csv').read_text(encoding='utf-8-sig').replace('has_attribute','run_shell')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.csv';p.write_text(raw,encoding='utf8')
            with self.assertRaises(Exception):load_rules(p)

if __name__ == '__main__': unittest.main()
