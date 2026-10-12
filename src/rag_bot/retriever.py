"""Retrieval layer: question -> the closest chunks from ChromaDB (with distances)."""
from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from rag_bot import config


@dataclass
class Retrieved:
    document: Document
    distance: float  # lower = closer match


class Retriever:
    def __init__(self, store, k: int = config.TOP_K):
        self.store = store
        self.k = k

    @classmethod
    def from_disk(cls, k: int = config.TOP_K) -> "Retriever":
        """Load the embedding model and the ChromaDB built by `python -m rag_bot.ingest`."""
        from rag_bot.embeddings import get_embeddings
        from rag_bot.ingest import load_vectorstore

        return cls(load_vectorstore(get_embeddings()), k)

    def search(self, question: str) -> list[Retrieved]:
        hits = self.store.similarity_search_with_score(question, k=self.k)
        return [Retrieved(doc, float(distance)) for doc, distance in hits]
