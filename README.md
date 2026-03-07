# seques

> AI Security Questionnaire Co-Pilot — Vendor Side

Stop spending 6–8 hours on security questionnaires. Upload your SOC 2, answer in 15 minutes.

## The problem

Every enterprise deal includes a security questionnaire. They take 6–8 hours to fill out manually, they ask the same 40 questions every time, and your SOC 2 already answers most of them.

## What this does

1. Upload your compliance docs (SOC 2, ISO 27001, security policies)
2. Upload the prospect's questionnaire (PDF, Excel, or paste)
3. AI reads your docs and drafts every answer
4. Review answers with **two independent confidence scores**:
   - **Evidence Coverage** — does your actual doc back this up?
   - **AI Certainty** — did the AI interpret it cleanly?
5. Edit, approve, export as Excel or PDF

Total time: 15–20 minutes instead of 6–8 hours.

## The differentiator

Every competitor (Responsive, RFPIO, Vanta) gives you an answer.

This tool tells you **how much to trust that answer** — and why.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY=sk-ant-...

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Tech stack

| Layer       | MVP                   |
|-------------|-----------------------|
| Frontend    | React + Tailwind      |
| Backend     | FastAPI (Python)      |
| AI          | Claude Sonnet (Anthropic) |
| PDF parsing | PyMuPDF               |
| Excel       | pandas + openpyxl     |
| Vector store| In-memory (Phase 1)   |
| Export      | openpyxl + ReportLab  |

## Architecture

```
seques/
├── backend/
│   ├── main.py        ← FastAPI app, session management, all routes
│   ├── models.py      ← Pydantic schemas (Question, Answer, ComplianceDoc)
│   ├── ingest.py      ← PDF extraction, doc-type detection
│   ├── parser.py      ← Questionnaire parsing (PDF / Excel / text → questions)
│   ├── engine.py      ← Answer generation + confidence scoring via Claude
│   └── export.py      ← Excel (colour-coded) and PDF export
└── frontend/
    └── src/
        ├── screens/Upload.jsx       ← Step 1+2: upload docs + questionnaire
        ├── screens/Processing.jsx   ← Step 3: live progress
        ├── screens/Review.jsx       ← Step 4: filter, edit, approve
        ├── screens/Export.jsx       ← Step 5: download
        └── components/QuestionCard.jsx
```

## Confidence flag logic

Two independent axes per answer:

| Coverage    | Certainty  | Meaning                              |
|-------------|------------|--------------------------------------|
| Covered     | High >80%  | Safe to send as-is                   |
| Covered     | Medium     | Evidence exists — check wording      |
| Partial     | High       | Real gap — add detail manually       |
| None        | Any        | Confirmed gap or missing doc         |
| Any         | Low <50%   | Always escalate to human             |

## Roadmap

- **Phase 1** (current) — Working prototype, full doc in context, in-memory
- **Phase 2** — Chunking + embeddings + RAG, per-answer evidence citations
- **Phase 3** — Auth, persistent doc storage, response library
- **Phase 4** — Gap reports, framework mapper (SOC 2 / ISO controls), tone control

## Environment variables

```
ANTHROPIC_API_KEY=sk-ant-...
```
