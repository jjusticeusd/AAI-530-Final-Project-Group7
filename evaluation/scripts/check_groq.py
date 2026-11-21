"""One bounded Groq smoke test; no keys or raw error bodies are printed."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    key = os.environ.get('GROQ_API_KEY', '').strip()
    if not key:
        env = ROOT / '.env'
        if env.exists():
            for line in env.read_text().splitlines():
                name, sep, value = line.partition('=')
                if sep and name.strip() == 'GROQ_API_KEY':
                    key = value.strip().strip('\"\'')
    if not key:
        print('No Groq key configured. Add it privately to the package .env file.')
        return 2
    model = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-20b')
    payload = {'model': model, 'messages': [{'role': 'user', 'content': 'Reply with only: connection successful'}], 'max_completion_tokens': 128, 'temperature': 0}
    req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'NCAA-Referee-Connection-Test/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        hints = {401: 'Check the key privately.', 403: 'Check provider permissions.', 404: 'Check model availability; set GROQ_MODEL to an available model.', 429: 'Rate limit or quota reached; check your Groq account.'}
        print(f'Groq request failed: HTTP {exc.code}. ' + hints.get(exc.code, 'Check provider status and request compatibility.'))
        return 1
    except (urllib.error.URLError, TimeoutError):
        print('Connection failed or timed out; check network access.')
        return 1
    choices = data.get('choices') or []
    content = choices[0].get('message', {}).get('content') if choices else None
    print('Groq responded. Model:', data.get('model', model))
    print('Nonempty assistant response:', bool(content))
    print('This verifies connectivity only, not football accuracy or the RAG pipeline.')
    return 0 if content else 1


if __name__ == '__main__':
    sys.exit(main())
