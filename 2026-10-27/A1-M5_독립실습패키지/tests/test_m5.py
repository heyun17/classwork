import sys
import unittest
from pathlib import Path
from importlib import import_module
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cleaner import clean_text, char_ngrams
build_documents=import_module('05_prepare_m2_documents').build_documents
class TestM5(unittest.TestCase):
    def test_cleaning(self):
        t=clean_text('  WCAG 2.4.4\n aria-label  좋지 않습니다 ')
        for s in ('WCAG 2.4.4','aria-label','좋지 않습니다'): self.assertIn(s,t)
    def test_ngrams(self):
        self.assertEqual(char_ngrams('배송이',2),['배송','송이'])
    def test_counts_and_proposed(self):
        a=build_documents();b=build_documents(True)
        self.assertEqual(len(a),7);self.assertEqual(len(b),8)
        self.assertEqual(sum(d['metadata']['status']=='proposed' for d in b),1)
    def test_metadata_and_paths(self):
        for d in build_documents(True):
            m=d['metadata']
            self.assertTrue(m['rule_id'] and m['node_id'] and m['tree_path'])
            self.assertEqual(m['preprocess_version'],'nfc-ws-v1')
            self.assertTrue(d['raw_text'] and d['clean_text'])
if __name__=='__main__':unittest.main()
