import json
import urllib.request

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "perplexity",
    "stream": False,
    "messages": [
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Give me 3 bullet points about local LLM inference."}
    ],
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    body = resp.read().decode("utf-8")
    print(body)