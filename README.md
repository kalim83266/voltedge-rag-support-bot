# VoltEdge RAG Support Bot

A customer support chatbot that answers **only from your business documents** — and says so when it doesn't know.

> All store data, contact details and policies in this repo are fictional, created for demo purposes.

## Live demo

Run locally and open `http://localhost:8000/ui/index.html` — see setup below.

## What makes it different from a plain ChatGPT chatbot

| | Typical AI chatbot | This bot |
|---|---|---|
| Source of answers | Model's training data (may hallucinate) | Only your uploaded documents |
| When answer not found | Often invents a confident wrong answer | Says "I don't know" |
| Answer traceability | None | Every answer shows the document section it came from |
| Cost per question | Full LLM call every time | Gate check first — LLM skipped when nothing relevant found |

## How it works

```
Customer question
      ↓
Retriever  →  ChromaDB (top-3 most relevant chunks)
      ↓
Distance gate  →  if top distance > 1.0: "I don't know" (no LLM call)
      ↓
Generator  →  OpenAI GPT (strict prompt: use only the chunks, cite sources)
      ↓
      if LLM says "not found": "I don't know"
      if LLM answers: answer + source references
```

## Tech stack

| Layer | Technology |
|---|---|
| PDF parsing & cleaning | pypdf |
| Text chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local, free) |
| Vector database | ChromaDB |
| Answer generation | OpenAI gpt-4.1-mini |
| API | FastAPI + uvicorn |
| Rate limiting | slowapi (10 req/min per IP) |
| Chat widget | Vanilla HTML/CSS/JS (no framework) |
| Tests | pytest (24 tests, no API key needed) |

## Project structure

```
voltedge-rag-support-bot/
├── data/raw/                   ← business documents (PDF)
├── src/rag_bot/
│   ├── config.py               ← all settings (override via .env)
│   ├── ingest.py               ← PDF → chunks → embeddings → ChromaDB
│   ├── embeddings.py           ← HuggingFace embedding model
│   ├── retriever.py            ← ChromaDB search
│   ├── generator.py            ← OpenAI prompt + structured output
│   ├── bot.py                  ← distance gate + full pipeline
│   ├── chat.py                 ← terminal chat interface
│   ├── evaluate.py             ← retrieval evaluation on test questions
│   └── api.py                  ← FastAPI endpoints + rate limiting
├── frontend/
│   └── index.html              ← chat widget (single file)
├── tests/                      ← 24 pytest tests (fake embeddings + fake LLM)
├── .env.example                ← copy to .env and add your OpenAI key
└── requirements.txt
```

## Setup

### 1. Clone and create environment

```bash
git clone https://github.com/kalim83266/voltedge-rag-support-bot.git
cd voltedge-rag-support-bot
conda create -n voltedge python=3.11 -y
conda activate voltedge
pip install -r requirements.txt
pip install -e .
```

### 2. Add your OpenAI key

```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS / Linux
```

Edit `.env` and set:

```
OPENAI_API_KEY=sk-...your_key_here...
```

### 3. Build the knowledge base

```bash
python -m rag_bot.ingest
```

This reads the PDFs, creates embeddings (downloads ~90 MB model on first run), and saves the vector database to `chroma_db/`.

### 4. Run tests

```bash
pytest
```

Expected: **24 passed**. No OpenAI key needed for tests.

### 5. Start the server

```bash
uvicorn rag_bot.api:app --reload --port 8000
```

Open `http://localhost:8000/ui/index.html` in your browser.

## Evaluate retrieval quality

```bash
python -m rag_bot.evaluate --k 3 --gate 1.0
```

Runs 22 test questions (answerable + not-in-documents + multi-section) against the database and reports top-1 accuracy, coverage and the distance gate's performance.

**Baseline results on the demo documents:**

```
Top-1 correct: 12/15
Expected sections found in top-3: 19/22
Gate at 1.0: stops 3/6 not-in-documents questions before the LLM,
             wrongly blocks 0/15 answerable ones
```

## Using with a different client's documents

1. Replace files in `data/raw/` with the client's PDFs
2. Run `python -m rag_bot.ingest` to rebuild the database
3. Run `python -m rag_bot.evaluate` and re-tune the gate if needed
4. Deploy — everything else stays the same

## Deploy to Render

1. Push repo to GitHub (keep `chroma_db/` and `.env` out of git — already in `.gitignore`)
2. Create a new Web Service on [render.com](https://render.com) and connect the repo
3. Set these values in Render's dashboard:

| Field | Value |
|---|---|
| Build Command | `pip install -r requirements.txt && pip install -e . && python -m rag_bot.ingest` |
| Start Command | `uvicorn rag_bot.api:app --host 0.0.0.0 --port $PORT` |

4. Add `OPENAI_API_KEY` as an environment variable in Render's dashboard
5. Render provides HTTPS automatically

**Note:** Free tier sleeps after 15 minutes of inactivity (first request takes ~30 seconds to wake). Use the paid tier ($7/month) for production.

## Known limitations

- Retrieval uses dense vector search only — questions that need exact keyword matching may miss the right section
- The gate threshold (1.0) is calibrated for the demo documents and the MiniLM model; re-run `evaluate` when switching documents or embedding models
- Multi-section questions (e.g. "what happens to my refund if I return an opened smartphone for a different color?") sometimes miss one of the required sections in top-3

## License

MIT — free to use, modify and deploy for commercial projects.
