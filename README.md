# Seques

> AI co-pilot for security questionnaires, built for the vendor side of the deal.

Every enterprise deal comes with a security questionnaire. Filling one in by hand takes 6–8 hours, the same 40 questions come up every time, and your SOC 2 report already answers most of them. Seques drafts every answer from your own compliance documents in about 15 minutes, and tells you how far to trust each one.

**Status:** v1.0.0-stable (March 2026). The full flow works end to end. The frontend is still deployed at [seques.vercel.app](https://seques.vercel.app), but the backend is not currently hosted, so the live demo is offline. It runs locally in about five minutes (see [Run it locally](#run-it-locally)).

## How it works

1. **Upload your evidence:** SOC 2 report, ISO 27001 certificate, security policies (PDF or DOCX).
2. **Upload the questionnaire:** PDF, Excel, or pasted text. Seques parses it into individual questions.
3. **Draft:** an LLM reads your documents and answers every question.
4. **Review:** each answer gets two independent scores (below). Filter, edit, approve.
5. **Export:** a colour-coded Excel file or a PDF, ready to send.

## What makes it different

Tools like Responsive, RFPIO and Vanta give you an answer. Seques also tells you **how much to trust it, and why**, using two separate scores:

- **Evidence coverage:** does your actual documentation back this answer up?
- **AI certainty:** did the model interpret the question and the evidence cleanly?

| Coverage | Certainty | What to do |
|---|---|---|
| Covered | High (>80%) | Safe to send as is |
| Covered | Medium | Evidence exists; check the wording |
| Partial | High | Real gap; add detail by hand |
| None | Any | Confirmed gap or missing document |
| Any | Low (<50%) | Always escalate to a human |

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React, Vite, Tailwind |
| Backend | FastAPI (Python) |
| LLM | Multi-provider through one wrapper: Groq (Llama 3.3 70B, default), Google (Gemini 2.0 Flash), Anthropic (Claude Haiku 4.5) |
| Parsing | PyMuPDF for PDF, pandas and openpyxl for Excel, DOCX support |
| Export | openpyxl (Excel), ReportLab (PDF) |
| Data | Supabase (schema and row-level security ready), in-memory sessions in v1 |
| Ops | Docker, Railway (backend), Vercel (frontend), Mixpanel analytics, structured logging, audit trail, rate limiting |
| Tests | 175 backend tests (pytest) across the API, engine, parser, ingest, LLM wrapper and audit log |

## Repository layout

```
seques/
├── backend/          FastAPI app
│   ├── main.py       routes and session handling
│   ├── llm.py        multi-provider LLM wrapper (Groq key pool, provider fallback)
│   ├── engine.py     answer generation and confidence scoring
│   ├── parser.py     questionnaire parsing (PDF / Excel / text → questions)
│   ├── ingest.py     document extraction and type detection
│   ├── export.py     Excel and PDF export
│   ├── security.py   security headers and rate limiting
│   ├── audit.py      audit trail
│   ├── migrations/   Supabase schema
│   └── tests/
├── frontend/src/
│   └── screens/      Landing → Auth → Upload → Processing → Review → Export
├── docs/             architecture, handover, runbook, compliance controls (SOC 2, ISO 27001, GDPR)
├── agents/           the AI agent definitions used to build the project, plus build-log blog posts
└── landing/          static landing page
```

## Run it locally

You need Python 3.9+, Node 18+, and an API key for Groq, Google or Anthropic.

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set LLM_PROVIDER and the matching API key
uvicorn main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
cp .env.example .env.local  # VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173. API docs are at http://localhost:8000/docs. The app is behind a simple access code (`seques2026` by default; set `VITE_ACCESS_CODE` to change it).

Supabase and Mixpanel are optional for local use. See `backend/.env.example` for every setting.

## Known limits

- Document text is capped at 32,000 characters in total (`DOC_CHAR_BUDGET`), so long SOC 2 reports are only partly read. Retrieval (RAG) is the next fix.
- Answers are generated one at a time by default (`ANSWER_CONCURRENCY=1`), which is stable but slow.
- The rate limiter is in memory, so it resets on restart and doesn't work across multiple workers.
- Authentication is a shared access code, not per-user accounts.

## Roadmap

1. Retrieval over full documents, with per-answer evidence citations
2. Parallel answer generation
3. Redis-backed rate limiting
4. Multi-user accounts (the Supabase tables and policies already exist)

## Build log

How it was built, and the decisions behind it, are written up in [`agents/blog/posts/`](agents/blog/posts/). Examples: why Groq over Anthropic as the default, compliance as code from day one, and the three production bugs fixed at v1.
