"""FastAPI backend for the VoltEdge support bot.

Start the server (project root, voltedge env active):
    uvicorn rag_bot.api:app --reload --port 8000

Endpoints:
    GET  /          → health check (JSON)
    GET  /health    → health check (JSON)
    POST /ask       → {"question": "..."} → {answer, sources, found, used_llm}
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_bot import config
from rag_bot.bot import SupportBot


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
    yield                    # server runs here
    print("Shutting down.")


# ── app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoltEdge Support Bot API",
    description="RAG chatbot that answers from VoltEdge Electronics documents.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # demo only — restrict to your domain in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# serve the frontend folder at /ui  (optional, for demo)
import os
_frontend = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/ui", StaticFiles(directory=_frontend, html=True), name="ui")


# ── endpoints ────────────────────────────────────────────────────────
@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "model": config.OPENAI_MODEL, "gate": config.DISTANCE_GATE}


@app.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest):
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
