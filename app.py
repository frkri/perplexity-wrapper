import json
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import perplexity


def load_cookies():
    cookies_file = Path("/cookies.json")
    if cookies_file.exists():
        cookies_raw = cookies_file.read_text(encoding="utf-8").strip()
        return json.loads(cookies_raw) if cookies_raw else None

    cookies_raw = ""
    return json.loads(cookies_raw) if cookies_raw else None


cookies = load_cookies()
client = perplexity.Client(cookies) if cookies else perplexity.Client()
MODEL_ID = "perplexity"

MODEL_DATA = {
    "id": MODEL_ID,
    "object": "model",
    "created": int(time.time()),
    "owned_by": "perplexity-wrapper",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Msg(BaseModel):
    role: str
    content: str


class ChatReq(BaseModel):
    model: str = "perplexity"
    messages: list[Msg]
    stream: bool = False


@app.get("/v1/models")
def list_models():
    return {"object": "list", "data": [MODEL_DATA]}


@app.get("/v1/models/{model_id}")
def get_model(model_id: str):
    if model_id != MODEL_ID:
        raise HTTPException(404, "model not found")
    return MODEL_DATA


@app.post("/v1/chat/completions")
def chat(req: ChatReq):
    if not req.messages:
        raise HTTPException(400, "messages required")

    query = "\n".join(f"{m.role}: {m.content}" for m in req.messages)
    mode, px_model = ("auto", None)
    created = int(time.time())

    if not req.stream:
        r = client.search(
            query,
            mode=mode,
            model=px_model,
            sources=["web"],
            files={},
            stream=False,
            language="en-US",
            follow_up=None,
            incognito=True,
        )
        text = (r or {}).get("answer", "")
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": created,
            "model": req.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def gen():
        cid = f"chatcmpl-{uuid.uuid4().hex}"
        stream = client.search(
            query,
            mode=mode,
            model=px_model,
            sources=["web"],
            files={},
            stream=True,
            language="en-US",
            follow_up=None,
            incognito=True,
        )
        for chunk in stream:
            piece = chunk.get("answer", "") if isinstance(chunk, dict) else (chunk or "")
            if piece:
                yield f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': req.model, 'choices': [{'index': 0, 'delta': {'content': piece}, 'finish_reason': None}]})}\n\n"
        yield f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': req.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")