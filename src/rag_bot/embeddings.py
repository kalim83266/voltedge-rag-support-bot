"""Embedding model factory (kept separate so the model can be swapped or faked in tests)."""
from rag_bot import config


def get_embeddings():
    # Imported lazily so that tests and tools that never embed do not need the heavy model.
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        # Normalised vectors make distances comparable (useful for the "I don't know" threshold later).
        encode_kwargs={"normalize_embeddings": True},
    )
