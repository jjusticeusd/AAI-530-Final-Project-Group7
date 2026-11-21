import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('pipeline',Path(__file__).resolve().parents[1]/'scripts/referee_pipeline.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Checks(unittest.TestCase):
 def test_forged_citation_rejected(self):
  a=dict(behavior='answer',ruling='x',foul=False,penalty_yards=0,enforcement=None,next_down=None,next_distance=None,citations=[{'rule_id':'99-99-99','pdf_page':1}],missing_facts=[],needs_review=False)
  self.assertIn('Citation not in supplied evidence',p.validate(a,[{'id':'7-2-2','page':88}]))
 def test_wrong_page_rejected(self):
  a=dict(behavior='answer',ruling='x',foul=False,penalty_yards=0,enforcement=None,next_down=None,next_distance=None,citations=[{'rule_id':'7-2-2','pdf_page':89}],missing_facts=[],needs_review=False)
  self.assertIn('Citation not in supplied evidence',p.validate(a,[{'id':'7-2-2','page':88}]))
 def test_pinned_corpus_has_no_answers_or_ar(self):
  docs=p.corpus();self.assertEqual(len(docs),352);self.assertFalse(any(x['id'].startswith(('NCAA','A.R.')) for x in docs))
 def test_backward_pass_rule_is_retrieved(self):
  self.assertIn('7-2-2',[x['id'] for x in p.retrieve('A backward pass hits the ground inbounds. Is it incomplete?',p.corpus(),4)])
if __name__=='__main__':unittest.main()
