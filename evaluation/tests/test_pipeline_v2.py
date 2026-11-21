import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v2',ROOT/'scripts/referee_pipeline_v2.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class V2Checks(unittest.TestCase):
 def test_missing_evidence_quote_is_rejected(self):
  a=dict(behavior='answer',ruling='Claim',foul=None,penalty_yards=None,enforcement=None,next_down=None,next_distance=None,citations=[dict(rule_id='7-2-2',pdf_page=88)],missing_facts=[],needs_review=False,evidence_basis=[dict(rule_id='7-2-2',supporting_text='fabricated excerpt')])
  self.assertIn('Evidence excerpt not in supplied rule',v.validate(a,[dict(id='7-2-2',page=88,text='the ball continues in play')]))
 def test_development_split_cannot_include_holdout(self):
  manifest=json.loads((ROOT/'eval/split_manifest.json').read_text())
  inputs=[json.loads(l) for l in (ROOT/'eval/dev_inputs.jsonl').read_text().splitlines()]
  self.assertEqual(len(inputs),30);self.assertTrue(set(x['id'] for x in inputs).isdisjoint(manifest['test_ids']))
 def test_kickoff_out_of_bounds_retrieves_kicking_team_rule(self):
  self.assertIn('6-2-1',[x['id'] for x in v.retrieve('An untouched kickoff goes out of bounds at B-10. What choices does the receiving team have?',v.corpus(),4)])
if __name__=='__main__':unittest.main()
