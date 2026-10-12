"""Retrieval evaluation: runs every question of tests/test_questions.md against the database.

Usage (project root, environment active, after `python -m rag_bot.ingest`):
    python -m rag_bot.evaluate                  # top-3 chunks, "I don't know" gate at 1.0
    python -m rag_bot.evaluate --k 5            # look at the top 5 chunks instead
    python -m rag_bot.evaluate --k 5 --gate 0.95

It answers two questions:
  1. Does the right section come back first (top-1) or at least within the top 3?
  2. How far apart are "answerable" and "not in the documents" questions in distance?
     That gap is what we use to choose the "I don't know" threshold.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field

from rag_bot import config

TEST_SHEET = config.BASE_DIR / "tests" / "test_questions.md"


@dataclass
class TestCase:
    __test__ = False  # tell pytest this is not a test class

    qid: str                                   # A1, B3, C2 ...
    question: str
    expected: set[tuple[int, int]] = field(default_factory=set)  # {(document no., section no.)}
    partial: bool = False                      # bot may give a partial answer (e.g. B2)

    @property
    def group(self) -> str:
        return self.qid[0]


@dataclass
class Row:
    case: TestCase
    top_distance: float
    got: list[tuple[int, int]]                 # top-k (document, section) pairs, best first

    @property
    def status(self) -> str:
        if not self.case.expected:
            return "fallback"
        if self.got and self.got[0] in self.case.expected:
            return "OK"
        return "IN TOP-K" if set(self.got) & self.case.expected else "MISS"


# --------------------------------------------------------------------------- parsing the test sheet
def parse_sources(text: str) -> set[tuple[int, int]]:
    """'Document 1, Section 3, Section 4 and Section 5' -> {(1,3), (1,4), (1,5)}"""
    expected: set[tuple[int, int]] = set()
    for part in re.split(r"(?=Document\s+\d)", text):
        doc = re.match(r"Document\s+(\d+)", part)
        if doc:
            for sec in re.findall(r"Section\s+(\d+)", part):
                expected.add((int(doc.group(1)), int(sec)))
    return expected


def parse_test_sheet(text: str) -> list[TestCase]:
    cases: list[TestCase] = []
    for block in re.split(r"^### ", text, flags=re.MULTILINE)[1:]:
        head = re.match(r"([ABC]\d+)\.(.*)", block)
        question = re.search(r"\*\*Question:\*\*\s*(.+)", block)
        if not (head and question):
            continue
        source = re.search(r"\*\*Source:\*\*\s*(.+)", block)
        cases.append(
            TestCase(
                qid=head.group(1),
                question=question.group(1).strip(),
                expected=parse_sources(source.group(1)) if source else set(),
                partial="partial" in head.group(2).lower(),
            )
        )
    return cases


# --------------------------------------------------------------------------- running and reporting
def evaluate(store, cases: list[TestCase], k: int = 3) -> list[Row]:
    rows = []
    for case in cases:
        hits = store.similarity_search_with_score(case.question, k=k)
        got = [(int(doc.metadata["source"][:2]), int(doc.metadata["section_number"])) for doc, _ in hits]
        rows.append(Row(case, float(hits[0][1]), got))
    return rows


def suggest_threshold(rows: list[Row]) -> tuple[float, float, float | None]:
    """Returns (largest top-1 distance of answerable questions,
                smallest top-1 distance of unanswerable questions,
                midpoint if the two groups do not overlap, else None)."""
    answerable = [r.top_distance for r in rows if r.case.expected]
    unanswerable = [r.top_distance for r in rows if not r.case.expected and not r.case.partial]
    worst_ok, best_bad = max(answerable), min(unanswerable)
    return worst_ok, best_bad, (round((worst_ok + best_bad) / 2, 2) if worst_ok < best_bad else None)


def print_report(rows: list[Row], k: int = 3, gate: float = 1.0) -> None:
    width = max(len(", ".join(f"{d}.{s}" for d, s in r.got)) for r in rows)
    print(f"\n{'ID':<4} {'dist':>6}  {'status':<9} {'top-' + str(k) + ' (doc.section)':<{max(width, 20)}} question")
    print("-" * (60 + max(width, 20)))
    for r in rows:
        topk = ", ".join(f"{d}.{s}" for d, s in r.got)
        expected = "" if not r.case.expected else "  expected " + ", ".join(f"{d}.{s}" for d, s in sorted(r.case.expected))
        note = " (partial answer)" if r.case.partial else ""
        print(f"{r.case.qid:<4} {r.top_distance:6.3f}  {r.status:<9} {topk:<{max(width, 20)}} {r.case.question[:55]}{note}{expected}")

    answerable = [r for r in rows if r.case.expected]
    unanswerable = [r for r in rows if not r.case.expected and not r.case.partial]
    top1 = sum(r.status == "OK" for r in answerable)
    covered = sum(len(set(r.got) & r.case.expected) for r in answerable)
    wanted = sum(len(r.case.expected) for r in answerable)
    print(f"\nTop-1 correct: {top1}/{len(answerable)}   |   expected sections found in top-{k}: {covered}/{wanted}")

    worst_ok, best_bad, mid = suggest_threshold(rows)
    print(f"Answerable questions: top-1 distance up to {worst_ok:.3f}")
    print(f"Not-in-documents questions: top-1 distance from {best_bad:.3f}")
    if mid is None:
        print("The two groups OVERLAP -> distance alone cannot separate them; the prompt must handle the fallback too.")
    else:
        print(f"They do not overlap. Candidate threshold: {mid}  (distance above this -> \"I don't know\")")

    wrongly = [r.case.qid for r in answerable if r.top_distance > gate]
    caught = [r.case.qid for r in unanswerable if r.top_distance > gate]
    print(f"\nGate at {gate}: stops {len(caught)}/{len(unanswerable)} not-in-documents questions before the LLM "
          f"({', '.join(caught) or '-'}), wrongly blocks {len(wrongly)}/{len(answerable)} answerable ones ({', '.join(wrongly) or '-'}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval on tests/test_questions.md")
    parser.add_argument("--k", type=int, default=3, help="how many chunks to retrieve per question (default 3)")
    parser.add_argument("--gate", type=float, default=1.0, help="distance above which the bot would answer \"I don't know\" without calling the LLM")
    args = parser.parse_args()

    from rag_bot.embeddings import get_embeddings
    from rag_bot.ingest import load_vectorstore

    cases = parse_test_sheet(TEST_SHEET.read_text(encoding="utf-8"))
    print(f"Loaded {len(cases)} test questions from {TEST_SHEET.name}")
    store = load_vectorstore(get_embeddings())
    print_report(evaluate(store, cases, k=args.k), k=args.k, gate=args.gate)


if __name__ == "__main__":
    main()
