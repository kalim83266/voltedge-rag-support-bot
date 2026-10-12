"""Central settings. Values can be overridden through environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "raw"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "voltedge_docs"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# --- answer generation -------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

TOP_K = int(os.getenv("TOP_K", "3"))                  # chunks handed to the LLM
DISTANCE_GATE = float(os.getenv("DISTANCE_GATE", "1.0"))  # above this: "I don't know" without calling the LLM

NOT_FOUND_MESSAGE = (
    "I couldn't find this information in the VoltEdge documents, so I don't want to guess. "
    "Please contact VoltEdge Customer Support for help."
)
