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

GROQ_MODELS = ["openai/gpt-oss-120b"]
OPENROUTER_MODELS = ["nvidia/nemotron-3-ultra-550b-a55b:free"]
OPENROUTER_OPTIONS = {
    "openai/gpt-oss-120b": {
        "reasoning_effort": "low",
        "provider": {"order": ["groq"], "allow_fallbacks": False},
    },
    "qwen/qwen3.8-27b": {
        "max_tokens": 10000,
        "provider": {"order": ["deepinfra"], "allow_fallbacks": False},
    },
}
OLLAMA_MODELS = {"gemma3:12b": {"temperature": 0}}
OLLAMA_NUM_CTX = 16384
MAX_OUTPUT_TOKENS = 3500
RETRIES = 3
COOLDOWN = 20
RETRY_CODES = {408, 429, 500, 502, 503, 524, 529}
CONNECTION_ERRORS = (
    groq.APIConnectionError,
    httpx.TransportError,
    urllib.error.URLError,
    TimeoutError,
)


def ollama_url():
    return os.environ.get("OLLAMA_URL") or "http://localhost:11434"


def ollama_post(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{ollama_url()}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def ollama_models():
    try:
        installed = {m["name"] for m in ollama_post("/api/tags")["models"]}
    except urllib.error.URLError:
        return []
    return [m for m in OLLAMA_MODELS if m in installed]


def checked(text, finish_reason):
    if finish_reason == "length":
        print("  (answer cut off at the output limit)")
    return text


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
        choice = completion.choices[0]
        return checked(choice.message.content, choice.finish_reason)

    return send


def make_openrouter(model):
    client = OpenRouter()

    def send(messages):
        response = client.chat.send(
            model=model,
            messages=messages,
            temperature=0,
            **{"max_tokens": MAX_OUTPUT_TOKENS, **OPENROUTER_OPTIONS.get(model, {})},
        )
        choice = response.choices[0]
        return checked(choice.message.content, choice.finish_reason)

    return send


def make_ollama(model):
    def send(messages):
        reply = ollama_post(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {**OLLAMA_MODELS[model], "num_ctx": OLLAMA_NUM_CTX},
            },
        )
        return checked(reply["message"]["content"], reply.get("done_reason"))

    return send


MAKERS = {"Groq": make_groq, "OpenRouter": make_openrouter, "Ollama": make_ollama}


def available():
    providers = {}
    if os.environ.get("OPENROUTER_API_KEY"):
        providers["OpenRouter"] = OPENROUTER_MODELS
    if os.environ.get("GROQ_API_KEY"):
        providers["Groq"] = GROQ_MODELS
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
    return (
        getattr(e, "headers", None)
        or getattr(getattr(e, "response", None), "headers", None)
        or {}
    )


def ask(send, messages, max_wait=None):
    for attempt in range(1, RETRIES + 1):
        try:
            return send(messages)
        except (groq.APIError, OpenRouterError, *CONNECTION_ERRORS) as e:
            status = error_status(e)
            if status is not None and status not in RETRY_CODES:
                print(f"  (request rejected: HTTP {status})")
                return None
            wait = float(error_headers(e).get("retry-after", COOLDOWN))
            if max_wait is not None and wait > max_wait:
                print(f"  (busy for {wait:.0f}s, giving up)")
                return None
            print(f"  (busy, retrying in {wait:.0f}s... {attempt}/{RETRIES})")
            time.sleep(wait)
    return None
