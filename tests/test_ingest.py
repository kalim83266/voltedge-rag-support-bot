"""Tests for the ingestion pipeline. They use a fake embedding model, so no download is needed."""
from pathlib import Path

import pytest

from rag_bot import config
from rag_bot.ingest import (
    build_chunks,
    build_vectorstore,
    clean_line,
    load_all_chunks,
    parse_document,
)

PDF_DIR = config.DATA_DIR


def test_clean_line_removes_invisible_characters():
    assert clean_line("1.\u200b  Standard   Return\u00a0Window ") == "1. Standard Return Window"


def test_parse_document_finds_sections_and_survives_page_breaks():
    lines = [
        "SAMPLE POLICY",
        "1. First Topic",
        "Some text that is cut",
        "in the middle of a sentence.",
        "10.Last Topic",  # missing space after the number
        "Final text with a question-",
        "answering example.",
    ]
    title, sections = parse_document(lines)
    assert title == "SAMPLE POLICY"
    assert [s.number for s in sections] == [1, 10]
    assert sections[0].text == "Some text that is cut in the middle of a sentence."
    assert sections[1].title == "Last Topic"
    assert "question-answering" in sections[1].text


def test_document_without_headings_becomes_one_section():
    title, sections = parse_document(["A plain letter", "It has no numbered headings.", "Just text."])
    assert len(sections) == 1 and sections[0].number == 0


def test_every_chunk_carries_title_and_section_header():
    chunks = build_chunks(PDF_DIR / "01_return_refund_policy.pdf")
    assert len(chunks) == 8  # one chunk per section for this document
    restocking = next(c for c in chunks if c.metadata["section_title"] == "Restocking Fee")
    assert restocking.page_content.startswith("RETURN & REFUND POLICY - 4. Restocking Fee")
    assert "15% restocking fee" in restocking.page_content


def test_all_pdfs_are_clean_and_complete():
    chunks = load_all_chunks(PDF_DIR)
    assert len(chunks) == 8 + 10 + 9
    assert len({c.metadata["chunk_id"] for c in chunks}) == len(chunks)  # ids are unique
    assert all("\u200b" not in c.page_content for c in chunks)
    shipping_10 = next(c for c in chunks if c.metadata["source"].startswith("02") and c.metadata["section_number"] == 10)
    assert shipping_10.metadata["section_title"] == "Delivery Problems"


def test_long_section_is_split_and_every_piece_keeps_its_header(monkeypatch):
    import rag_bot.ingest as ingest

    long_text = " ".join(f"Sentence number {i} about returns." for i in range(60))
    fake_lines = ["TITLE", "1. Long Topic", long_text, "2. Short Topic", "Short text."]
    monkeypatch.setattr(ingest, "read_pdf_lines", lambda path: fake_lines)

    chunks = ingest.build_chunks(Path("fake.pdf"), chunk_size=300, chunk_overlap=30)
    long_chunks = [c for c in chunks if c.metadata["section_number"] == 1]
    assert len(long_chunks) > 1
    assert all(c.page_content.startswith("TITLE - 1. Long Topic\n") for c in long_chunks)
    assert len({c.metadata["chunk_id"] for c in chunks}) == len(chunks)


def test_vectorstore_roundtrip(tmp_path):
    from langchain_core.embeddings import DeterministicFakeEmbedding

    chunks = load_all_chunks(PDF_DIR)
    store = build_vectorstore(chunks, DeterministicFakeEmbedding(size=64), persist_dir=tmp_path / "db")
    assert store._collection.count() == len(chunks)
    hits = store.similarity_search("anything", k=3)
    assert len(hits) == 3 and {"source", "section_title"} <= set(hits[0].metadata)
