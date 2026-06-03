import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"


def call_ollama(prompt: str, system: str = "") -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    if system:
        payload["system"] = system

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data.get("response", "").strip()