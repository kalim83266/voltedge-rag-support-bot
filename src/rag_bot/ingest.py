"""Ingestion pipeline: PDF -> clean text -> section-aware chunks -> embeddings -> ChromaDB.

Usage (from the project root, with the conda environment active):
    python -m rag_bot.ingest                      # rebuild the knowledge base from data/raw/*.pdf
    python -m rag_bot.ingest --query "your question"   # test retrieval on the existing database
"""
from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from rag_bot import config

# Invisible characters that word processors / PDF exporters like to leave behind.
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)

# A section heading looks like "4. Restocking Fee" (also tolerates a missing space: "10.Delivery").
_HEADING_RE = re.compile(r"^(\d{1,2})\.\s*([A-Z][^.:;]{1,70})$")


@dataclass
class Section:
    number: int  # 0 when the document has no numbered sections
    title: str
    text: str


# --------------------------------------------------------------------------- reading & cleaning
def clean_line(line: str) -> str:
    line = line.translate(_INVISIBLE).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", line).strip()


def read_pdf_lines(path: Path) -> list[str]:
    """Return cleaned, non-empty text lines of a PDF (pages are joined in order)."""
    reader = PdfReader(str(path))
    lines: list[str] = []
    for page in reader.pages:
        lines.extend(clean_line(l) for l in (page.extract_text() or "").splitlines())
    return [l for l in lines if l]


def _join_lines(lines: list[str]) -> str:
    """Join wrapped lines into one paragraph. A trailing hyphen joins without a space
    ("question-" + "answering" -> "question-answering")."""
    text = ""
    for line in lines:
        if not text:
            text = line
        elif text.endswith("-") and line[:1].isalpha():
            text += line
        else:
            text += " " + line
    return text.strip()


def parse_document(lines: list[str]) -> tuple[str, list[Section]]:
    """Split a document into (title, numbered sections). Falls back to a single
    section when the document has no numbered headings (typical for client files)."""
    if not lines:
        return "", []
    title, body = lines[0], lines[1:]
    if _HEADING_RE.match(title):  # no separate title line: first line is already a heading
        title, body = "", lines

    sections: list[Section] = []
    current_head: tuple[int, str] | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if current_head and buffer:
            sections.append(Section(current_head[0], current_head[1], _join_lines(buffer)))
        buffer = []

    for line in body:
        m = _HEADING_RE.match(line)
        if m:
            flush()
            current_head = (int(m.group(1)), m.group(2).strip())
        else:
            buffer.append(line)
    flush()

    if len(sections) < 2:  # not a structured document -> treat everything as one section
        return title, [Section(0, "", _join_lines(body))]
    return title, sections


# --------------------------------------------------------------------------- chunking
def build_chunks(
    path: Path,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[Document]:
    """Turn one PDF into LangChain Documents. Every chunk starts with its document title
    and section heading so the retrieved text always carries its own context."""
    title, sections = parse_document(read_pdf_lines(path))
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    docs: list[Document] = []
    for sec in sections:
        header_parts = [p for p in (title, f"{sec.number}. {sec.title}" if sec.number else "") if p]
        header = " - ".join(header_parts)
        pieces = splitter.split_text(sec.text) if len(sec.text) > chunk_size else [sec.text]
        for idx, piece in enumerate(pieces):
            docs.append(
                Document(
                    page_content=f"{header}\n{piece}" if header else piece,
                    metadata={
                        "source": path.name,
                        "doc_title": title,
                        "section_number": sec.number,
                        "section_title": sec.title,
                        "chunk_index": idx,
                        "chunk_id": f"{path.stem}-s{sec.number}-c{idx}",
                    },
                )
            )
    return docs


def load_all_chunks(data_dir: Path = config.DATA_DIR) -> list[Document]:
    pdfs = sorted(data_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in {data_dir}")
    chunks: list[Document] = []
    for pdf in pdfs:
        file_chunks = build_chunks(pdf)
        print(f"  {pdf.name}: {len(file_chunks)} chunks")
        chunks.extend(file_chunks)
    return chunks


# --------------------------------------------------------------------------- vector store
def build_vectorstore(documents: list[Document], embeddings, persist_dir: Path = config.CHROMA_DIR):
    """Create a fresh ChromaDB collection from the documents (the old one is deleted first)."""
    from langchain_chroma import Chroma

    if persist_dir.exists():
        shutil.rmtree(persist_dir)
    store = Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )
    store.add_documents(documents, ids=[d.metadata["chunk_id"] for d in documents])
    return store


def load_vectorstore(embeddings, persist_dir: Path = config.CHROMA_DIR):
    from langchain_chroma import Chroma

    if not persist_dir.exists():
        raise FileNotFoundError("No database found. Run `python -m rag_bot.ingest` first.")
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )


def show_matches(store, question: str, k: int = 3) -> None:
    """Print the top-k chunks for a question (lower distance = closer match)."""
    print(f'\nQuestion: "{question}"')
    for rank, (doc, distance) in enumerate(store.similarity_search_with_score(question, k=k), start=1):
        meta = doc.metadata
        print(f"\n#{rank}  distance={distance:.3f}  {meta['source']}  section {meta['section_number']}: {meta['section_title']}")
        print("   " + doc.page_content.replace("\n", "\n   ")[:400])


# --------------------------------------------------------------------------- command line
def main() -> None:
    parser = argparse.ArgumentParser(description="Build or test the VoltEdge knowledge base.")
    parser.add_argument("--query", help="Only test retrieval for this question (no re-ingestion).")
    parser.add_argument("--k", type=int, default=3, help="How many chunks to show (default 3).")
    args = parser.parse_args()

    from rag_bot.embeddings import get_embeddings

    print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
    embeddings = get_embeddings()

    if args.query:
        show_matches(load_vectorstore(embeddings), args.query, args.k)
        return

    print(f"Reading PDFs from {config.DATA_DIR}")
    chunks = load_all_chunks()
    print(f"Embedding {len(chunks)} chunks and writing to {config.CHROMA_DIR} ...")
    build_vectorstore(chunks, embeddings)
    print("Done. Test retrieval with:\n  python -m rag_bot.ingest --query \"How long do I have to return an opened laptop?\"")


if __name__ == "__main__":
    main()
