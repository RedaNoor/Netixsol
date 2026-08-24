"""
FastAPI wrapper around the LangGraph AFL application.

Run: uvicorn api:app --reload --port 8000
Docs: http://localhost:8000/docs

POST /chat
  {"message": "who won the 2024 grand final", "conversation_id": "abc123"}
  -> {"response": "...", "intent": "retrieval", "tools_called": [...],
      "is_prediction": false, "latency_ms": 842.1}

conversation_id is caller-supplied and maps directly to the LangGraph thread_id — the same id
across calls carries conversation memory forward, same as run_chat.py.
"""
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graph import build_graph
import logging_setup as logs

app = FastAPI(title="AFL Assistant API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_graph = build_graph()

# --- minimal in-memory rate limiting (per Task 1's abuse-handling consideration) ---
_request_log = {}  # conversation_id -> list of request timestamps
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20


def _check_rate_limit(conversation_id: str):
    now = time.time()
    history = [t for t in _request_log.get(conversation_id, []) if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(history) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail=(
            f"Rate limit exceeded — max {RATE_LIMIT_MAX_REQUESTS} requests per "
            f"{RATE_LIMIT_WINDOW_SECONDS}s per conversation. Try again shortly."))
    history.append(now)
    _request_log[conversation_id] = history


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str]
    tools_called: list
    is_prediction: bool
    conversation_id: str
    latency_ms: float


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    conversation_id = req.conversation_id or str(uuid.uuid4())
    _check_rate_limit(conversation_id)

    start = time.monotonic()
    error = None
    try:
        result = _graph.invoke(
            {"user_query": req.message},
            config={"configurable": {"thread_id": conversation_id}},
        )
    except Exception as e:
        error = str(e)
        result = {"final_response": "Something went wrong processing that request. Please try again.",
                  "intent": None, "tool_name": None}

    latency_ms = (time.monotonic() - start) * 1000
    intent = result.get("intent")
    tool_name = result.get("tool_name")
    tools_called = [tool_name] if tool_name else []
    token_usage = logs.extract_token_usage(result)

    logs.log_request(
        conversation_id=conversation_id, query=req.message, intent=intent,
        tools_called=tools_called, latency_ms=latency_ms, token_usage=token_usage, error=error,
    )

    return ChatResponse(
        response=result.get("final_response", "No response generated."),
        intent=intent,
        tools_called=tools_called,
        is_prediction=intent in ("prediction_match", "prediction_player"),
        conversation_id=conversation_id,
        latency_ms=round(latency_ms, 1),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
