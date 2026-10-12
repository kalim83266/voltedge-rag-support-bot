"""Tests for the bot logic. A fake retriever and a fake LLM are used, so no key or model is needed."""
import pytest
from langchain_core.documents import Document

from rag_bot import config
from rag_bot.bot import SupportBot
from rag_bot.generator import BotAnswer, build_context, make_llm
from rag_bot.retriever import Retrieved


def chunk(number, title, text, distance):
    meta = {"doc_title": "RETURN & REFUND POLICY", "source": "01_return_refund_policy.pdf",
            "section_number": number, "section_title": title}
    return Retrieved(Document(page_content=f"RETURN & REFUND POLICY - {number}. {title}\n{text}", metadata=meta), distance)


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def search(self, question):
        return self.hits


class FakeLLM:
    """Mimics a chat model: with_structured_output() returns itself, invoke() returns a prepared answer."""

    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return self.reply


HITS = [chunk(3, "Product-Specific Rules", "Opened laptops: 14 days.", 0.7),
        chunk(1, "Standard Return Window", "30 days.", 1.0),
        chunk(4, "Restocking Fee", "15% fee.", 1.1)]


def test_build_context_numbers_the_passages():
    context = build_context(HITS)
    assert context.startswith("[1] RETURN & REFUND POLICY - 3. Product-Specific Rules")
    assert "\n\n[2] " in context and "\n\n[3] " in context


def test_far_question_is_blocked_without_calling_the_llm():
    llm = FakeLLM(BotAnswer(found=True, answer="should not be used"))
    bot = SupportBot(FakeRetriever([chunk(1, "X", "text", distance=1.2)]), llm=llm)
    answer = bot.ask("Can you gift wrap?")
    assert answer.text == config.NOT_FOUND_MESSAGE and not answer.used_llm and llm.calls == []


def test_found_answer_returns_only_the_sources_the_llm_used():
    llm = FakeLLM(BotAnswer(found=True, answer="14 days for an opened laptop.", source_ids=[1, 3, 1, 9]))
    answer = SupportBot(FakeRetriever(HITS), llm=llm).ask("How long to return an opened laptop?")
    assert answer.found and answer.used_llm
    assert answer.text == "14 days for an opened laptop."
    assert [s.section for s in answer.sources] == [3, 4]  # duplicates and unknown ids are ignored
    assert answer.sources[0].label == "RETURN & REFUND POLICY - 3. Product-Specific Rules"


def test_llm_says_not_found_gives_standard_message_without_sources():
    llm = FakeLLM(BotAnswer(found=False, answer="made up warranty text", source_ids=[1]))
    answer = SupportBot(FakeRetriever(HITS), llm=llm).ask("How long is the warranty?")
    assert answer.text == config.NOT_FOUND_MESSAGE and answer.sources == [] and answer.used_llm and not answer.found


def test_missing_source_ids_fall_back_to_the_best_match():
    llm = FakeLLM(BotAnswer(found=True, answer="30 days.", source_ids=[]))
    answer = SupportBot(FakeRetriever(HITS), llm=llm).ask("Return window?")
    assert [s.section for s in answer.sources] == [3]


def test_prompt_contains_question_and_numbered_context():
    llm = FakeLLM(BotAnswer(found=True, answer="ok", source_ids=[1]))
    SupportBot(FakeRetriever(HITS), llm=llm).ask("Return window?")
    system, human = llm.calls[0]
    assert system[0] == "system" and "ONLY" in system[1]
    assert "[1] RETURN & REFUND POLICY" in human[1] and "Customer question: Return window?" in human[1]


def test_empty_question_and_missing_key(monkeypatch):
    assert SupportBot(FakeRetriever(HITS), llm=FakeLLM(None)).ask("   ").text == "Please type your question."
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        make_llm()
