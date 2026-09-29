# Chat With Your Docs

A custom RAG (Retrieval-Augmented Generation) pipeline: ingest thousands of
company documents, ask questions, get precise answers grounded in your docs
with source citations.

## How it works

1. **Ingest** — parses PDFs, Word docs, PowerPoint, HTML, and text files;
   splits them into overlapping chunks along paragraph boundaries; embeds
   each chunk with Voyage AI; stores everything in Postgres (pgvector).
2. **Retrieve** — for each question, runs vector search *and* keyword search,
   merges results, and reranks them with Voyage's reranker for precision.
3. **Generate** — sends the top chunks + question to Claude, instructed to
   answer only from the provided text and cite sources.

## Setup

### 1. Install Postgres with pgvector

```bash
# macOS
brew install postgresql pgvector

# or use Docker
docker run -d --name chatdocs-pg -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 pgvector/pgvector:pg16
```

Create the database and schema:

```bash
createdb chatdocs
psql chatdocs -f schema.sql
```

### 2. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# edit .env: add your ANTHROPIC_API_KEY and VOYAGE_API_KEY
```

Get a Voyage AI key at https://www.voyageai.com (the first 200 million tokens
of embedding usage are free for every account, so at personal-doc-set scale
you likely won't pay anything).

**Choosing your answer-generation model:** set `LLM_PROVIDER` to either:

- `anthropic` (default) — Claude, paid but cheap (fractions of a cent per
  question). Best at reliably following the "answer only from context, cite
  sources" instructions.
- `groq` — free, no credit card, very fast inference on open-weight models
  (Llama 3.3, Qwen, gpt-oss). Rate-limited to roughly 30 requests/minute and
  1,000/day on the free tier, which is plenty for personal use. Slightly
  more variance in following the citation format exactly, since it's not
  Claude under the hood.

Get a Groq key at https://console.groq.com/keys — no payment info required.
You only need to set the API key for whichever provider you choose; the
other one can be left blank in `.env`.

### 4. Ingest your documents

```bash
python ingest_cli.py /path/to/your/company/docs
```

This recursively finds all `.pdf`, `.docx`, `.pptx`, `.html`, `.txt`, `.md`
files, parses, chunks, embeds, and stores them. Re-run it any time you add
new documents (it doesn't currently de-duplicate re-ingested files — see
"Next steps" below).

### 5. Run the chat server

```bash
uvicorn app:app --reload
```

### 6. Ask questions

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our refund policy for enterprise customers?"}'
```

Response:

```json
{
  "answer": "Enterprise customers are eligible for a full refund within 30 days... (refund-policy.pdf, Page 2)",
  "sources": ["refund-policy.pdf (Page 2)"]
}
```

## Project structure

```
chat-with-docs/
├── schema.sql          # Postgres + pgvector table definitions
├── config.py            # env-driven settings
├── db.py                 # connection pool, insert + hybrid search queries
├── embeddings.py     # Voyage AI embed + rerank wrapper
├── retrieval.py        # hybrid search + rerank orchestration
├── generate.py        # Claude API call with citation-focused prompt
├── ingest_cli.py       # command-line ingestion script
├── ingest/
│   ├── parser.py        # per-filetype text extraction
│   └── chunker.py      # paragraph-aware chunking with overlap
└── app.py                 # FastAPI /chat endpoint
```

## Tuning for precision

- **Chunk size** (`CHUNK_TARGET_TOKENS` in `.env`): smaller chunks (~200-300
  tokens) give more precise retrieval for fact-lookup questions; larger
  chunks (~500-800) preserve more context for "explain X" questions.
- **RERANK_TOP_K**: how many chunks actually reach Claude. Higher = more
  context but higher cost and risk of dilution; 5-10 is a good range.
- **Hybrid search weighting**: currently vector and keyword hits are merged
  with vector hits taking priority on collision. If you find exact-term
  lookups (product codes, names) underperforming, increase `KEYWORD_TOP_K`.

## Next steps you may want to add

- **De-duplication on re-ingest**: currently re-running `ingest_cli.py` on
  the same folder creates duplicate entries. Add a check on `source_path`
  before inserting, or delete-and-reinsert per file.
- **Incremental ingestion**: watch a folder and auto-ingest new/changed
  files.
- **Access control**: not needed for single-user use, but if you ever share
  this, add auth to `app.py` and per-document permissions in the schema.
- **A simple frontend**: `app.py` is API-only. A minimal HTML/JS chat page
  can be added to call `/chat` directly.
- **Conversation history**: `/chat` is currently single-turn (no memory
  between questions). For follow-ups, pass prior Q&A pairs into the Claude
  call in `generate.py`.
