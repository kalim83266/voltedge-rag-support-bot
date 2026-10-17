"""FastAPI backend for the VoltEdge support bot.

Start the server (project root, voltedge env active):
    uvicorn rag_bot.api:app --reload --port 8000

Endpoints:
    GET  /          → health check (JSON)
    GET  /health    → health check (JSON)
    POST /ask       → {"question": "..."} → {answer, sources, found, used_llm}
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from rag_bot import config
from rag_bot.bot import SupportBot


# ── rate limiter ─────────────────────────────────────────────────────
# 10 requests per minute per IP (demo setting — raise for production)
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])


# ── request / response models ────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class SourceOut(BaseModel):
    label: str
    section: int


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    found: bool
    used_llm: bool
    top_distance: float | None = None


# ── lifespan: load bot once at startup ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading VoltEdge support bot ...")
    app.state.bot = SupportBot.from_disk()
    print("Bot ready.")
    yield
    print("Shutting down.")


# ── app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoltEdge Support Bot API",
    description="RAG chatbot that answers from VoltEdge Electronics documents.",
    version="1.0.0",
    lifespan=lifespan,
)

# attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # demo only — restrict to your domain in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# serve the frontend folder at /ui
_frontend = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/ui", StaticFiles(directory=_frontend, html=True), name="ui")


# ── endpoints ────────────────────────────────────────────────────────
@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "model": config.OPENAI_MODEL, "gate": config.DISTANCE_GATE}


@app.post("/ask", response_model=AskResponse)
@limiter.limit("10/minute")
async def ask(request: Request, body: AskRequest):
    bot: SupportBot = app.state.bot
    try:
        result = bot.ask(body.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AskResponse(
        answer=result.text,
        sources=[SourceOut(label=s.label, section=s.section) for s in result.sources],
        found=result.found,
        used_llm=result.used_llm,
        top_distance=result.top_distance,
    )
