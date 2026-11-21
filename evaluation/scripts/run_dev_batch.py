"""Resume fixed v2 development batch; honor bounded provider rate-limit waits."""
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'eval/results/groq_dev30_v2_120b.jsonl'
for cycle in range(12):
    if output.exists():
        rows=[json.loads(l) for l in output.read_text().splitlines()]
        last=rows[-1] if rows else {}
        if last.get('error')=='HTTP 429':
            try:wait=max(15,float(last.get('retry_after') or 15)+2)
            except ValueError:wait=20
            if wait>60:
                print('Provider requests a wait over 60 seconds; batch paused with results saved.',flush=True);sys.exit(2)
            print(f'Waiting {wait:.0f}s before resuming after provider rate limit.',flush=True);time.sleep(wait)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/referee_pipeline_v2.py'),'--dev','--model','openai/gpt-oss-120b','--output',str(output)])
    rows=[json.loads(l) for l in output.read_text().splitlines()] if output.exists() else []
    completed={x['case_id'] for x in rows if x.get('error') is None}
    print(f'Completed responses: {len(completed)}/30',flush=True)
    if len(completed)==30:sys.exit(0)
    if not rows or rows[-1].get('error')!='HTTP 429':sys.exit(result.returncode or 1)
print('Reached bounded resume limit; results saved.',flush=True)
sys.exit(2)
