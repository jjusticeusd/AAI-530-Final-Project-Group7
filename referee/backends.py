import json
import os
import time
import urllib.error
import urllib.request

import groq
import httpx
from groq import Groq
from openrouter import OpenRouter
from openrouter.errors import OpenRouterError

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
OPENROUTER_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
]
OLLAMA_MODELS = {"gemma3:12b": {"temperature": 0}}
OLLAMA_NUM_CTX = 16384
MAX_OUTPUT_TOKENS = 1200
RETRIES = 3
COOLDOWN = 20
RETRY_CODES = {408, 429, 500, 502, 503, 524, 529}
CONNECTION_ERRORS = (groq.APIConnectionError, httpx.TransportError, urllib.error.URLError, TimeoutError)


def ollama_url():
    return os.environ.get("OLLAMA_URL") or "http://localhost:11434"


def ollama_post(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(f"{ollama_url()}{path}", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def ollama_models():
    try:
        installed = {m["name"] for m in ollama_post("/api/tags")["models"]}
    except urllib.error.URLError:
        return []
    return [m for m in OLLAMA_MODELS if m in installed]


def make_groq(model):
    client = Groq()

    def send(messages):
        completion = client.chat.completions.create(
            model=model,
            temperature=0,
            reasoning_effort="low",
            max_completion_tokens=MAX_OUTPUT_TOKENS,
            messages=messages,
        )
        return completion.choices[0].message.content

    return send


def make_openrouter(model):
    client = OpenRouter()

    def send(messages):
        response = client.chat.send(model=model, messages=messages, temperature=0, max_tokens=MAX_OUTPUT_TOKENS)
        return response.choices[0].message.content

    return send


def make_ollama(model):
    def send(messages):
        reply = ollama_post("/api/chat", {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {**OLLAMA_MODELS[model], "num_ctx": OLLAMA_NUM_CTX},
        })
        return reply["message"]["content"]

    return send


MAKERS = {"Groq": make_groq, "OpenRouter": make_openrouter, "Ollama": make_ollama}


def available():
    providers = {}
    if os.environ.get("GROQ_API_KEY"):
        providers["Groq"] = GROQ_MODELS
    if os.environ.get("OPENROUTER_API_KEY"):
        providers["OpenRouter"] = OPENROUTER_MODELS
    local = ollama_models()
    if local:
        providers["Ollama"] = local
    return [f"{p} / {m}" for p, models in providers.items() for m in models]


def backend(label):
    provider, model = label.split(" / ", 1)
    return MAKERS[provider](model)


def error_status(e):
    return getattr(e, "status_code", None) or getattr(e, "code", None)


def error_headers(e):
    return getattr(e, "headers", None) or getattr(getattr(e, "response", None), "headers", None) or {}


def ask(send, messages):
    for attempt in range(1, RETRIES + 1):
        try:
            return send(messages)
        except (groq.APIError, OpenRouterError, *CONNECTION_ERRORS) as e:
            status = error_status(e)
            if status is not None and status not in RETRY_CODES:
                print(f"  (request rejected: HTTP {status})")
                return None
            wait = float(error_headers(e).get("retry-after", COOLDOWN))
            print(f"  (busy, retrying in {wait:.0f}s... {attempt}/{RETRIES})")
            time.sleep(wait)
    return None
