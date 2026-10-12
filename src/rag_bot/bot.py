"""The support bot: retrieval -> distance gate -> LLM -> answer with source references."""
from __future__ import annotations

from dataclasses import dataclass, field

from rag_bot import config
from rag_bot.generator import generate, make_llm
from rag_bot.retriever import Retrieved, Retriever


@dataclass
class Source:
    label: str   # e.g. "RETURN & REFUND POLICY - 3. Product-Specific Rules"
    file: str
    section: int


@dataclass
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)
    found: bool = False
    used_llm: bool = False
    top_distance: float | None = None


def _source_from(item: Retrieved) -> Source:
    meta = item.document.metadata
    title = meta.get("doc_title") or meta.get("source", "document")
    number, section_title = meta.get("section_number", 0), meta.get("section_title", "")
    label = f"{title} - {number}. {section_title}" if number else title
    return Source(label=label, file=meta.get("source", ""), section=number)


class SupportBot:
    def __init__(self, retriever: Retriever, llm=None, gate: float = config.DISTANCE_GATE):
        self.retriever = retriever
        self._llm = llm
        self.gate = gate

    @classmethod
    def from_disk(cls) -> "SupportBot":
        return cls(Retriever.from_disk())

    @property
    def llm(self):
        if self._llm is None:  # created only when needed, so gated questions work without an API key
            self._llm = make_llm()
        return self._llm

    def ask(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            return Answer("Please type your question.")

        retrieved = self.retriever.search(question)
        top = retrieved[0].distance if retrieved else None

        # Layer 1: nothing close enough in the documents -> no LLM call, no cost.
        if top is None or top > self.gate:
            return Answer(config.NOT_FOUND_MESSAGE, top_distance=top)

        # Layer 2: the LLM may only use the retrieved passages and must say so when they don't help.
        result = generate(self.llm, question, retrieved)
        if not result.found:
            return Answer(config.NOT_FOUND_MESSAGE, used_llm=True, top_distance=top)

        used = []
        for number in result.source_ids:
            if 1 <= number <= len(retrieved) and retrieved[number - 1] not in used:
                used.append(retrieved[number - 1])
        if not used:  # the LLM did not name its sources: show the best match instead of nothing
            used = [retrieved[0]]
        return Answer(result.answer.strip(), [_source_from(r) for r in used], True, True, top)
