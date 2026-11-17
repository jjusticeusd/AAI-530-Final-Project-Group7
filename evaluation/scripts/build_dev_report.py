"""Review-only report joins approved development keys to saved outputs."""
import collections
import json
import statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    keys=[json.loads(l) for l in (ROOT/'eval/dev_scenarios.jsonl').read_text().splitlines()]
    source=ROOT/'eval/results/groq_dev30_v2_120b.jsonl'
    outputs=[json.loads(l) for l in source.read_text().splitlines()] if source.exists() else []
    latest={x['case_id']:x for x in outputs}
    lines=['# Development run v2 - review report','',f'Expected cases: {len(keys)}. Attempted unique cases: {len(latest)}. Model: Groq openai/gpt-oss-120b.','', 'This is an internal development diagnostic. Generated answers have not been approved by Timothy. Existence/excerpt checks do not establish semantic citation support or correctness. Null expected penalty values are not scored as zero. No reserved final test inputs or keys are read by this report.','']
    successful=0;check_pass=0;flags=collections.Counter()
    for c in keys:
        out=latest.get(c['id']);lines += [f"## {c['id']}",'',f"**Question:** {c['question']}",'',f"**Approved answer:** {c['expected_answer']}",'']
        if not out:lines+=['**Status:** Not attempted yet.',''];continue
        if out.get('error'):lines += [f"**Provider error:** {out['error']}",''];continue
        successful+=1
        ans=out.get('parsed_output')
        if not isinstance(ans,dict):lines+=['**Status:** No structured object.',''];continue
        notes=list(out.get('validation_errors',[]))
        citations=ans.get('citations',[])
        if isinstance(citations,list) and citations and all(isinstance(x,str) for x in citations):
            notes=['Citation format invalid: strings lack required rule-ID/page objects.' if n=='Citation not in supplied evidence' else n for n in notes]
            supplied=set(out['retrieved_chunk_ids'])
            if any(x not in supplied for x in citations):notes.append('At least one cited rule ID is absent from supplied evidence.')
        if not notes:check_pass+=1
        if ans.get('behavior')!=c['expected_behavior']:notes.append('Behavior differs from key; adjudicate equivalent uncertainty wording.')
        if c['expected_foul'] is not None and ans.get('foul')!=c['expected_foul']:notes.append('Foul status differs from key.')
        if c['expected_penalty_yards'] is not None and ans.get('penalty_yards')!=c['expected_penalty_yards']:notes.append('Penalty-yard field differs from key; adjudicate no-penalty null versus zero separately.')
        for note in set(notes):flags[note]+=1
        lines += [f"**Model answer:** {ans.get('ruling')}",'',f"**Enforcement:** {ans.get('enforcement')}; next down={ans.get('next_down')}, distance={ans.get('next_distance')}; foul={ans.get('foul')}; penalty yards={ans.get('penalty_yards')}",'',f"**Citations:** {json.dumps(ans.get('citations'),ensure_ascii=False)}",'',f"**Retrieved rules:** {', '.join(out['retrieved_chunk_ids'])}",'',f"**Review flags:** {'; '.join(dict.fromkeys(notes)) if notes else 'No automated flags; human correctness/support review still required.'}",'','**Timothy grading:** [ ] Correct [ ] Partly correct [ ] Incorrect [ ] Needs discussion','']
    summary={'expected_cases':len(keys),'attempted_unique_cases':len(latest),'completed_api_responses':successful,'structure_and_excerpt_checks_pass':check_pass,'automated_flag_counts':dict(flags),'api_failure_records':sum(bool(x.get('error')) for x in outputs),'model_responses_with_validation_flags':successful-check_pass,'median_latency_seconds':round(statistics.median([x['latency_seconds'] for x in latest.values() if x.get('error') is None]),3) if successful else None,'total_recorded_prompt_tokens':sum((x.get('usage') or {}).get('prompt_tokens',0) for x in outputs),'total_recorded_completion_tokens':sum((x.get('usage') or {}).get('completion_tokens',0) for x in outputs),'human_accuracy':None,'reserved_test_run':False,'run_complete':len(latest)==len(keys) and successful==len(keys)}
    (ROOT/'DEV_RUN_V2_REVIEW.md').write_text('\n'.join(lines).rstrip()+'\n')
    (ROOT/'eval/results/dev30_v2_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
if __name__=='__main__':main()
