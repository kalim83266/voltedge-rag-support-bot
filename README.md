# VoltEdge Support Bot (RAG demo)

A retrieval-augmented support chatbot that answers customer questions **only from company documents**
(return policy, shipping policy, FAQ) and says "I don't know" when the answer is not in them.

> All store data, contact details and policies are fictional, created for demo purposes.

**Status:** Phase 2 of 5 — document ingestion (PDF -> chunks -> embeddings -> ChromaDB).
Answer generation, API and chat widget are added in the next phases.

## Setup (Miniconda)

```bash
conda create -n voltedge python=3.11 -y
conda activate voltedge
pip install -r requirements.txt
pip install -e .
copy .env.example .env      # Windows (use "cp" on macOS/Linux); then add your own key later
```

## Build the knowledge base

```bash
python -m rag_bot.ingest
```

## Test retrieval

```bash
python -m rag_bot.ingest --query "How long do I have to return an opened laptop?"
```

## Run the tests

```bash
pytest
```

## Project layout

```
data/raw/            sample PDFs (fictional)
src/rag_bot/         application code (config, embeddings, ingest)
tests/               automated tests + question sheet used to evaluate the bot
```
