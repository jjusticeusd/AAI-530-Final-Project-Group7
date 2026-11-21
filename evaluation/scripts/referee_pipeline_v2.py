"""Local prototype: pinned rule-only BM25 retrieval, Groq, structural citation checks.
Generation reads input-only files, never answer keys. Standard library only.
"""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def tokens(s):
    return re.findall(r'[a-z0-9]+', s.lower())

def expand(question):
    terms = json.loads((ROOT.parent/'referee/terminology.json').read_text())['entries']
    additions=[]
    for term in terms:
        if re.search(r'(?<!\w)'+re.escape(term['phrase'])+r'(?!\w)',question,re.I):
            additions.extend(term['expand_to'])
    return question+' '+' '.join(additions)

def corpus():
    manifest=json.loads((ROOT/'source_manifest.json').read_text())
    pdf=ROOT/'.reference/rulebook.pdf'
    if digest(pdf.read_bytes()) != manifest['sha256']:
        raise ValueError('Rulebook hash differs from pinned manifest')
    # Derived only from the rulebook; no scenarios, keys, or Approved Rulings.
    chunks=json.loads((ROOT/'.reference/chunks.json').read_text())
    return [{'id':x['id'],'page':x['page'],'text':'\n'.join(x['lines'])} for x in chunks if x['kind']=='rule' and len(x['lines'])>1]

def retrieve(question, docs, k=8):
    query=collections.Counter(tokens(expand(question)))
    bags=[collections.Counter(tokens(x['text'])) for x in docs]
    lengths=[sum(b.values()) for b in bags]; avg=sum(lengths)/max(1,len(lengths))
    df=collections.Counter(w for b in bags for w in b)
    scores=[]
    # Domain concept routing expands searches, without consulting answer keys.
    hints=set()
    for pattern, ids in [(r'backward pass|lateral|fumble', ['2-19-2','7-2-1','7-2-2']), (r'fair.catch|muff', ['2-8-1','6-5-1','6-5-2']), (r'pass interference|\bdpi\b|\bopi\b', ['7-3-8','7-3-9']), (r'kickoff.*out of bounds|free kick.*out of bounds', ['6-2-1'])]:
        if re.search(pattern,question,re.I):hints.update(ids)
    for doc,bag,n in zip(docs,bags,lengths):
        score=0.0
        for word,qfreq in query.items():
            tf=bag[word]
            if tf:
                idf=math.log(1+(len(docs)-df[word]+0.5)/(df[word]+0.5))
                score+=idf*(tf*2.5)/(tf+1.5*(0.25+0.75*n/avg))*min(qfreq,2)
        if re.search(r'(?<!\d)'+re.escape(doc['id'])+r'(?![\d-])',question):score+=15
        if doc['id'] in hints:score+=12
        scores.append((score,doc))
    return [dict(doc,retrieval_score=round(score,5)) for score,doc in sorted(scores,key=lambda x:(-x[0],x[1]['id']))[:k] if score>0]

def key():
    result=os.environ.get('GROQ_API_KEY','').strip()
    if not result and (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text().splitlines():
            name,sep,value=line.partition('=')
            if sep and name.strip()=='GROQ_API_KEY':result=value.strip().strip('\"\'')
    if not result:raise ValueError('No Groq key configured')
    return result

def validate(answer,evidence):
    errors=[]
    required={'behavior','ruling','foul','penalty_yards','enforcement','next_down','next_distance','citations','missing_facts','needs_review'}
    if not isinstance(answer,dict):return ['Response is not an object']
    if required-set(answer):errors.append('Missing response fields')
    if answer.get('behavior') not in {'answer','clarify','out_of_scope','refuse_fabrication','insufficient_evidence'}:errors.append('Invalid behavior')
    if not isinstance(answer.get('ruling'),str) or not answer.get('ruling'):errors.append('Missing ruling text')
    if type(answer.get('needs_review')) is not bool:errors.append('Invalid review flag')
    if answer.get('behavior') in {'clarify','insufficient_evidence'} and answer.get('needs_review') is not True:errors.append('Uncertainty requires review')
    if answer.get('next_down') is not None and (type(answer['next_down']) is not int or not 1<=answer['next_down']<=4):errors.append('Next down out of range')
    if answer.get('foul') is not None and type(answer['foul']) is not bool:errors.append('Invalid foul type')
    for field in ['penalty_yards','next_down','next_distance']:
        if answer.get(field) is not None and (type(answer[field]) is not int or answer[field]<0):errors.append('Invalid '+field)
    if answer.get('enforcement') is not None and not isinstance(answer['enforcement'],str):errors.append('Invalid enforcement')
    if not isinstance(answer.get('missing_facts'),list):errors.append('Invalid missing_facts')
    citations=answer.get('citations');allowed={(x['id'],x['page']) for x in evidence}
    if not isinstance(citations,list):errors.append('Invalid citations array');citations=[]
    for c in citations:
        if not isinstance(c,dict) or (c.get('rule_id'),c.get('pdf_page')) not in allowed:errors.append('Citation not in supplied evidence')
    if answer.get('behavior')=='answer' and not citations:errors.append('Substantive answer has no citations')
    if answer.get('behavior')=='answer':
        basis=answer.get('evidence_basis')
        if not isinstance(basis,list) or not basis:errors.append('Missing evidence basis')
        else:
            texts={x['id']:' '.join(x['text'].split()).lower() for x in evidence}
            for item in basis:
                if not isinstance(item,dict):errors.append('Invalid evidence basis');continue
                quote=' '.join(str(item.get('supporting_text','')).split()).lower()
                if not quote or quote not in texts.get(item.get('rule_id'),''):errors.append('Evidence excerpt not in supplied rule')
    return errors

def generate(question,docs,model,k=4):
    evidence=retrieve(question,docs,k)
    # Explicit user-specified evidence boundaries supersede normal retrieval.
    if re.search(r'only rule 1\b',question,re.I) and re.search(r'only that context',question,re.I):
        evidence=[x for x in docs if x['id'].startswith('1-1')][:2]
    prompt=(ROOT/'prompts/system_v2.txt').read_text()
    context=json.dumps(evidence,ensure_ascii=False)
    payload={'model':model,'temperature':0,'reasoning_effort':'low','max_completion_tokens':2200,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'question':question,'evidence':evidence},ensure_ascii=False)}]}
    record={'question':question,'provider':'Groq','model':model,'prompt_version':'v2','prompt_hash':digest(prompt.encode()),'terminology_hash':digest((ROOT.parent/'referee/terminology.json').read_bytes()),'corpus_hash':digest(json.dumps(docs,sort_keys=True).encode()),'pipeline_hash':digest(Path(__file__).read_bytes()),'retrieval_k':k,'retrieval_mode':'BM25_rule_only','retrieved_chunk_ids':[x['id'] for x in evidence],'retrieved_context_hash':digest(context.encode()),'retrieved_evidence':evidence,'attempts':0,'error':None,'raw_output':None,'parsed_output':None,'validation_errors':[],'actual_cost_usd':None}
    started=time.monotonic()
    for attempt in range(2):
        record['attempts']+=1
        req=urllib.request.Request('https://api.groq.com/openai/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json','User-Agent':'NCAA-Referee-Prototype/1.0'})
        try:
            with urllib.request.urlopen(req,timeout=75) as response:data=json.load(response)
            record['model']=data.get('model',model);record['usage']=data.get('usage');record['finish_reason']=data['choices'][0].get('finish_reason')
            record['raw_output']=data['choices'][0]['message'].get('content')
            try:record['parsed_output']=json.loads(record['raw_output'] or '')
            except (ValueError,TypeError):record['error']='Invalid JSON response';break
            record['validation_errors']=validate(record['parsed_output'],evidence)
            if record['finish_reason']=='length':record['validation_errors'].append('Output token limit reached')
            if record['validation_errors'] and isinstance(record['parsed_output'],dict):
                record['parsed_output']['needs_review']=True
            break
        except urllib.error.HTTPError as exc:
            record['error']='HTTP '+str(exc.code)
            try:
                provider_error=json.loads(exc.read()).get('error',{})
                record['provider_error_code']=provider_error.get('code')
            except (ValueError,AttributeError):pass
            record['retry_after']=exc.headers.get('retry-after')
            if attempt==0 and exc.code in {429,500,502,503,504}:
                try:wait=min(20,max(1,float(exc.headers.get('retry-after','5'))))
                except ValueError:wait=5
                time.sleep(wait);record['error']=None;continue
            break
        except (urllib.error.URLError,TimeoutError):record['error']='Connection failed or timed out';break
    record['latency_seconds']=round(time.monotonic()-started,3)
    # Structural existence is not semantic citation support or ruling accuracy.
    record['schema_and_evidence_checks_pass']=bool(record['parsed_output']) and not record['validation_errors']
    record['citation_existence_pass']=isinstance(record['parsed_output'],dict) and isinstance(record['parsed_output'].get('citations'),list) and 'Citation not in supplied evidence' not in record['validation_errors']
    record['human_review_status']='pending';return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--question');parser.add_argument('--dev',action='store_true');parser.add_argument('--limit',type=int);parser.add_argument('--retrieve-only',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--model',default=os.environ.get('GROQ_MODEL','openai/gpt-oss-20b'));args=parser.parse_args()
    docs=corpus()
    if args.dev:
        inputs=[json.loads(l) for l in (ROOT/'eval/dev_inputs.jsonl').read_text().splitlines()]
    elif args.question:inputs=[{'id':'manual','question':args.question,'split':'manual'}]
    else:parser.error('Choose --question or --dev')
    if args.limit:inputs=inputs[:args.limit]
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True)
    done=set()
    if args.output and args.output.exists():
        for line in args.output.read_text().splitlines():
            rec=json.loads(line)
            if rec.get('error') is None and rec.get('model')==args.model and rec.get('prompt_hash')==digest((ROOT/'prompts/system_v2.txt').read_bytes()) and rec.get('corpus_hash')==digest(json.dumps(docs,sort_keys=True).encode()) and rec.get('terminology_hash')==digest((ROOT.parent/'referee/terminology.json').read_bytes()) and rec.get('question')==next((x['question'] for x in inputs if x['id']==rec.get('case_id')),None) and rec.get('pipeline_hash')==digest(Path(__file__).read_bytes()):done.add(rec['case_id'])
    for case in inputs:
        if case['id'] in done:continue
        if args.retrieve_only:
            print(case['id'],[x['id'] for x in retrieve(case['question'],docs)]);continue
        rec=generate(case['question'],docs,args.model);rec.update(case_id=case['id'],split=case['split'],timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        if args.output:
            with args.output.open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
        print(case['id'],json.dumps({'error':rec['error'],'validation_errors':rec['validation_errors'],'answer':rec['parsed_output']},ensure_ascii=False),flush=True)
        if rec.get('error')=='HTTP 429':
            print('Stopped batch at provider rate limit; results saved for resume.',flush=True);break
        if args.dev:time.sleep(12)

if __name__=='__main__':main()
