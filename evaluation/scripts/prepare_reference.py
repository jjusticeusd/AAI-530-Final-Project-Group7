"""Prepare ignored rulebook files; verify pinned bytes before parsing."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
from referee import ingest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path);args=parser.parse_args()
    manifest=json.loads((ROOT/'source_manifest.json').read_text())
    folder=ROOT/'.reference';folder.mkdir(exist_ok=True);pdf=folder/'rulebook.pdf'
    if args.pdf:
        if args.pdf.resolve()!=pdf.resolve():shutil.copyfile(args.pdf,pdf)
    elif not pdf.exists():
        request=urllib.request.Request(manifest['source_url'],headers={'User-Agent':'NCAA-Referee-Reference/1.0'})
        with urllib.request.urlopen(request,timeout=90) as response:pdf.write_bytes(response.read())
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=manifest['sha256']:
        raise SystemExit('PDF hash mismatch. Stop and review the edition/source; do not silently replace the answer key.')
    texts=ingest.pages(pdf)
    a,b,_=ingest.part_starts(texts)
    chunks=ingest.split_rules(texts,a,b)
    (folder/'chunks.json').write_text(json.dumps(chunks,ensure_ascii=False)+'\n')
    print(f'Pinned PDF verified: {len(texts)} pages; {sum(len(c["lines"])>1 for c in chunks)} rule chunks; no Approved Rulings indexed.')
if __name__=='__main__':main()
