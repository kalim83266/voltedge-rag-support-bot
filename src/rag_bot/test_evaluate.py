"""Tests for the evaluation helpers (no embedding model needed)."""
from rag_bot.evaluate import (
    TEST_SHEET,
    evaluate,
    parse_sources,
    parse_test_sheet,
    print_report,
    suggest_threshold,
)
from rag_bot.ingest import build_vectorstore, load_all_chunks


def test_parse_sources_handles_several_sections_and_documents():
    assert parse_sources("Document 1, Section 3 — Product-Specific Rules.") == {(1, 3)}
    assert parse_sources("Document 1, Section 3, Section 4 and Section 5.") == {(1, 3), (1, 4), (1, 5)}
    assert parse_sources("Document 2, Section 10 and Document 1, Section 6.") == {(2, 10), (1, 6)}


def test_test_sheet_is_parsed_completely():
    cases = {c.qid: c for c in parse_test_sheet(TEST_SHEET.read_text(encoding="utf-8"))}
    assert len(cases) == 10 + 7 + 5
    assert cases["A1"].expected == {(1, 1)}
    assert cases["C5"].expected == {(2, 10), (1, 6)}
    assert cases["B1"].expected == set() and not cases["B1"].partial
    assert cases["B2"].partial  # international shipping may get a partial answer


def test_evaluation_runs_end_to_end_with_fake_embeddings(tmp_path, capsys):
    from langchain_core.embeddings import DeterministicFakeEmbedding

    store = build_vectorstore(load_all_chunks(), DeterministicFakeEmbedding(size=64), persist_dir=tmp_path / "db")
    cases = parse_test_sheet(TEST_SHEET.read_text(encoding="utf-8"))
    rows = evaluate(store, cases)
    assert len(rows) == len(cases)
    assert all(len(r.got) == 3 for r in rows)
    suggest_threshold(rows)  # must not crash
    print_report(rows)
    assert "Top-1 correct" in capsys.readouterr().out
