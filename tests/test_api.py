"""Tests for the FastAPI endpoints (no real bot, no OpenAI key needed)."""
import pytest
from fastapi.testclient import TestClient

from rag_bot.bot import Answer, Source
from rag_bot.api import app


class FakeBot:
    """Returns scripted answers without touching ChromaDB or OpenAI."""
    def ask(self, question: str) -> Answer:
        q = question.lower()
        if "laptop" in q and "return" in q:
            return Answer(
                "14 calendar days for an opened laptop.",
                [Source("RETURN & REFUND POLICY - 3. Product-Specific Rules", "01_return_refund_policy.pdf", 3)],
                found=True, used_llm=True, top_distance=0.705,
            )
        if "warranty" in q:
            return Answer(
                "I couldn't find this information in the VoltEdge documents, so I don't want to guess. "
                "Please contact VoltEdge Customer Support for help.",
                found=False, used_llm=True, top_distance=0.976,
            )
        return Answer("I couldn't find this information.", found=False, used_llm=False, top_distance=1.2)


@pytest.fixture
def client():
    app.state.bot = FakeBot()
    return TestClient(app)


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_root_returns_ok(client):
    assert client.get("/").status_code == 200


def test_ask_found_answer(client):
    r = client.post("/ask", json={"question": "How long to return an opened laptop?"})
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is True
    assert "14 calendar days" in data["answer"]
    assert data["sources"][0]["section"] == 3
    assert data["top_distance"] == pytest.approx(0.705, abs=1e-3)


def test_ask_not_found_answer(client):
    r = client.post("/ask", json={"question": "What is the warranty?"})
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is False and data["sources"] == []


def test_ask_rejects_empty_question(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_rejects_missing_field(client):
    assert client.post("/ask", json={}).status_code == 422


def test_ask_rejects_too_long_question(client):
    assert client.post("/ask", json={"question": "x" * 501}).status_code == 422
