"""
Seques — Security Questionnaire Co-Pilot
API server (FastAPI)

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json
"""

import asyncio
import io
import json
import os
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

import analytics
import audit
import database
from engine import answer_question, build_doc_context
from export import export_excel, export_pdf
from ingest import ingest_docx, ingest_manual, ingest_pdf
from llm import PROVIDER_KEYS, PROVIDER_MODELS
from models import Answer, AnswerStatus, AnswerTone, EvidenceCoverage
from observability import logger
from parser import parse_excel_questionnaire, parse_pdf_questionnaire, parse_text_questionnaire
# TODO: re-enable after fixing middleware exception handling
# from observability import RequestTracingMiddleware
# from security import RateLimitMiddleware, SecurityHeadersMiddleware

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Seques — Security Questionnaire Co-Pilot",
    description=(
        "AI-powered API that ingests vendor compliance documents and generates "
        "draft answers to security questionnaires. Supports Anthropic, Groq, and Google AI.\n\n"
        "**Swagger UI** is this page. **ReDoc** at `/redoc`. **OpenAPI JSON** at `/openapi.json`.\n\n"
        "All mutating endpoints emit structured audit log entries (SOC 2 CC7.2, GDPR Art 30)."
    ),
    version=os.getenv("APP_VERSION", "1.0.0"),
    contact={"name": "Seques Engineering", "email": "eng@seques.io"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "meta", "description": "Health, version, provider info"},
        {"name": "sessions", "description": "Session lifecycle"},
        {"name": "docs", "description": "Upload compliance evidence documents"},
        {"name": "questionnaire", "description": "Upload the prospect's questionnaire"},
        {"name": "answers", "description": "Retrieve and edit AI-generated answers"},
        {"name": "export", "description": "Download filled questionnaire"},
        {"name": "audit", "description": "Audit trail (read-only)"},
    ],
)

# TODO (open issue): restore SecurityHeadersMiddleware, RateLimitMiddleware, RequestTracingMiddleware
# Temporarily disabled — custom middleware was intercepting exceptions before CORS headers
# could be applied, causing ERR_FAILED on all API calls from the frontend.
# Tracked in: agents/security/agent.md + agents/shared/decisions.md
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: ensures unhandled exceptions return JSON with CORS headers applied."""
    logger.error("unhandled_exception", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


# ---------------------------------------------------------------------------
# In-memory session store (Phase 1 — Supabase persistence in Phase 2)
# ---------------------------------------------------------------------------

class Session:
    def __init__(self, session_id: str, provider: str, client_ip: str = ""):
        self.id = session_id
        self.provider = provider
        self.client_ip = client_ip
        self.docs = []
        self.questions = []
        self.answers: Dict[str, Answer] = {}
        self.processing = False
        self.processed_count = 0
        self.total_questions = 0
        self.questionnaire_filename: Optional[str] = None
        self.questionnaire_type: Optional[str] = None
        self.started_at = time.time()
        self.processing_started_at: Optional[float] = None


sessions: Dict[str, Session] = {}

_CONCURRENCY_RAW = int(os.getenv("ANSWER_CONCURRENCY", "1"))
ANSWER_CONCURRENCY = min(_CONCURRENCY_RAW, 20)
if _CONCURRENCY_RAW > 20:
    import warnings
    warnings.warn(f"ANSWER_CONCURRENCY={_CONCURRENCY_RAW} exceeds max of 20; clamped to 20.")

# Delay between questions to stay well under TPM limits (seconds)
QUESTION_DELAY_S = float(os.getenv("QUESTION_DELAY_S", "1.5"))

# Dedicated executor for fire-and-forget DB saves — lives outside answer engine
# so its shutdown doesn't block session.processing = False
_db_save_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="db-save")


def get_session(session_id: str) -> Session:
    session = sessions.get(session_id)
    if not session:
        # Try to restore from Supabase (handles server restarts)
        session = _restore_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _restore_session(session_id: str) -> "Session | None":
    """Reload a session from Supabase after a server restart."""
    row = database.load_session_row(session_id)
    if not row:
        return None

    from models import AnswerFormat, AnswerStatus, AnswerTone, EvidenceCoverage
    session = Session(session_id=row["id"], provider=row["provider"], client_ip=row.get("client_ip", ""))
    session.questionnaire_type = row.get("questionnaire_type")
    session.questionnaire_filename = row.get("questionnaire_filename")
    session.total_questions = row.get("total_questions", 0)
    session.processing = row.get("processing", False)

    # Reload questions
    from models import Question
    q_rows = database.load_questions(session_id)
    session.questions = [
        Question(
            id=r["id"], text=r["text"],
            answer_format=AnswerFormat(r["answer_format"]) if r.get("answer_format") else AnswerFormat.freeform,
            category=r.get("category"), original_row=r.get("original_row"),
        )
        for r in q_rows
    ]

    # Reload answers
    a_rows = database.load_answers(session_id)
    for r in a_rows:
        try:
            answer = Answer(
                question_id=r["question_id"], question_text=r.get("question_text", ""),
                draft_answer=r.get("draft_answer", ""),
                evidence_coverage=EvidenceCoverage(r["evidence_coverage"]),
                coverage_reason=r.get("coverage_reason", ""),
                ai_certainty=r.get("ai_certainty", 0),
                certainty_reason=r.get("certainty_reason", ""),
                evidence_sources=r.get("evidence_sources") or [],
                suggested_addition=r.get("suggested_addition"),
                answer_tone=AnswerTone(r["answer_tone"]),
                needs_review=r.get("needs_review", True),
                status=AnswerStatus(r.get("status", "draft")),
            )
            session.answers[answer.question_id] = answer
        except Exception:
            pass

    session.processed_count = len(session.answers)
    sessions[session_id] = session
    logger.info("session_restored_from_supabase", extra={"session_id": session_id})
    return session


# ---------------------------------------------------------------------------
# Meta routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"], summary="Health check")
def health():
    """Liveness probe. Returns 200 if the process is up."""
    return {"status": "ok", "version": os.getenv("APP_VERSION", "1.0.0")}


@app.get("/api/providers", tags=["meta"], summary="List configured LLM providers")
def list_providers():
    """
    Returns all supported LLM providers, which have their API key configured,
    and which is currently the default (set by LLM_PROVIDER env var).
    """
    default = os.getenv("LLM_PROVIDER", "anthropic").lower()
    result = []
    for name, key_var in PROVIDER_KEYS.items():
        result.append({
            "id": name,
            "model": PROVIDER_MODELS[name],
            "configured": bool(os.getenv(key_var)),
            "default": name == default,
        })
    return {"providers": result}


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class CreateSessionBody(BaseModel):
    provider: Optional[str] = None


@app.post(
    "/api/sessions",
    tags=["sessions"],
    summary="Create a new session",
    status_code=201,
)
def create_session(body: Optional[CreateSessionBody] = None, request: Request = None):
    """
    Creates an isolated session. All uploads and answers are scoped to this session.
    Optionally pass `{"provider": "groq"}` body to override the server default.

    **Phase 2**: sessions will be persisted to Supabase.
    """
    session_id = str(uuid.uuid4())
    provider = (((body.provider if body else None) or os.getenv("LLM_PROVIDER", "anthropic"))).lower()
    ip = request.client.host if request and request.client else "unknown"
    sessions[session_id] = Session(session_id, provider, client_ip=ip)

    audit.emit("session.create", actor=ip, resource_type="session", resource_id=session_id,
               detail={"provider": provider})
    analytics.session_created(session_id, provider, ip)
    logger.info("session_created", extra={"session_id": session_id, "provider": provider})
    database.save_session(sessions[session_id])

    return JSONResponse(
        {"session_id": session_id, "provider": provider},
        status_code=201,
    )


# ---------------------------------------------------------------------------
# Compliance docs
# ---------------------------------------------------------------------------

SUPPORTED_DOC_TYPES = {".pdf", ".docx"}
SUPPORTED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",  # some browsers send this for .docx
    },
}
MAX_DOC_BYTES = 50 * 1024 * 1024  # 50 MB


@app.post(
    "/api/sessions/{session_id}/docs",
    tags=["docs"],
    summary="Upload compliance evidence documents (PDF or Word .docx)",
)
async def upload_docs(session_id: str, files: List[UploadFile] = File(...), request: Request = None):
    """
    Upload one or more compliance documents (SOC 2, ISO 27001, security policies).
    Supported formats: PDF and Word (.docx). Unsupported types are returned in `skipped`.
    Maximum file size: 50 MB per file.

    **GDPR note**: document text is held in-memory only and never persisted to disk.
    """
    session = get_session(session_id)
    ip = request.client.host if request and request.client else session.client_ip

    added = []
    skipped = []
    for file in files:
        suffix = os.path.splitext(file.filename)[1].lower()
        if suffix not in SUPPORTED_DOC_TYPES:
            skipped.append(file.filename)
            continue

        data = await file.read()

        # SEC-009: reject oversized files before writing to disk
        if len(data) > MAX_DOC_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{file.filename}' exceeds the 50 MB limit ({len(data) // (1024*1024)} MB).",
            )

        # SEC-011: validate MIME type against allowlist for the given extension
        content_type = (file.content_type or "").split(";")[0].strip()
        allowed_mimes = SUPPORTED_MIME_TYPES.get(suffix, set())
        if content_type and content_type not in allowed_mimes:
            skipped.append(file.filename)
            continue

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                doc = ingest_pdf(tmp_path, file.filename)
            else:
                try:
                    doc = ingest_docx(tmp_path, file.filename)
                except Exception as e:
                    # Catch corrupt/invalid .docx (BadZipFile, etc.) as a 400
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not parse '{file.filename}': {e}. Ensure it is a valid, unencrypted Word document.",
                    )
            session.docs.append(doc)
            added.append({"filename": doc.filename, "doc_type": doc.doc_type, "pages": doc.pages})
        finally:
            os.unlink(tmp_path)

    audit.emit("docs.upload", actor=ip, resource_type="session", resource_id=session_id,
               detail={"filenames": [f["filename"] for f in added], "count": len(added), "skipped": skipped})
    analytics.docs_uploaded(session_id, len(added), [f["doc_type"] for f in added])

    return {"docs": added, "skipped": skipped}


@app.post(
    "/api/sessions/{session_id}/manual-doc",
    tags=["docs"],
    summary="Add a compliance document as plain text",
)
async def upload_manual_doc(session_id: str, text: str = Form(...), request: Request = None):
    """Paste raw text (e.g. a policy excerpt) as a compliance evidence source."""
    session = get_session(session_id)
    ip = request.client.host if request and request.client else session.client_ip
    doc = ingest_manual(text)
    session.docs.append(doc)

    audit.emit("docs.upload_manual", actor=ip, resource_type="session", resource_id=session_id,
               detail={"chars": len(text)})

    return {"ok": True}


# ---------------------------------------------------------------------------
# Questionnaire
# ---------------------------------------------------------------------------

@app.post(
    "/api/sessions/{session_id}/questionnaire",
    tags=["questionnaire"],
    summary="Upload the prospect's questionnaire",
)
async def upload_questionnaire(
    session_id: str,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    request: Request = None,
):
    """
    Accepts:
    - **PDF** — AI extracts and classifies each question
    - **Excel (.xlsx/.xls)** — auto-detects the question column
    - **Pasted text** — AI parses questions from raw text

    Returns the list of parsed questions for preview.
    """
    session = get_session(session_id)
    ip = request.client.host if request and request.client else session.client_ip

    if file and file.filename:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                questions = parse_pdf_questionnaire(tmp_path, provider=session.provider)
                session.questionnaire_type = "pdf"
            elif suffix in (".xlsx", ".xls"):
                questions = parse_excel_questionnaire(tmp_path)
                session.questionnaire_type = "excel"
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
        finally:
            os.unlink(tmp_path)

        session.questionnaire_filename = file.filename

    elif text and text.strip():
        questions = parse_text_questionnaire(text.strip(), provider=session.provider)
        session.questionnaire_type = "text"

    else:
        raise HTTPException(status_code=400, detail="Provide a file or pasted text")

    session.questions = questions
    session.total_questions = len(questions)
    database.save_questions(session_id, questions)
    database.save_session(session)

    audit.emit("questionnaire.upload", actor=ip, resource_type="session", resource_id=session_id,
               detail={"question_count": len(questions), "source": session.questionnaire_type,
                       "filename": session.questionnaire_filename})
    analytics.questionnaire_uploaded(session_id, len(questions), session.questionnaire_type or "text",
                                     session.provider)

    return {
        "question_count": len(questions),
        "questions": [q.model_dump() for q in questions],
    }


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

@app.post(
    "/api/sessions/{session_id}/process",
    tags=["answers"],
    summary="Start AI answer generation (async)",
)
async def process_questionnaire(
    session_id: str,
    background_tasks: BackgroundTasks,
    request: Request = None,
):
    """
    Kicks off background processing. Poll `/status` for progress.
    Returns immediately with `{"status": "processing", "total": N}`.

    Requires at least one compliance doc and one questionnaire to be uploaded.
    """
    session = get_session(session_id)
    ip = request.client.host if request and request.client else session.client_ip

    required_key = PROVIDER_KEYS.get(session.provider, "ANTHROPIC_API_KEY")
    if not os.getenv(required_key):
        raise HTTPException(
            status_code=400,
            detail=f"{required_key} not configured for provider '{session.provider}'. Set it in backend/.env.",
        )
    if session.processing:
        raise HTTPException(status_code=409, detail="Session is already being processed. Wait for it to complete.")
    if not session.docs:
        raise HTTPException(status_code=400, detail="No compliance docs uploaded")
    if not session.questions:
        raise HTTPException(status_code=400, detail="No questionnaire uploaded")

    session.processing = True
    session.processed_count = 0
    session.answers = {}
    session.processing_started_at = time.time()
    database.mark_processing_started(session_id)

    audit.emit("processing.start", actor=ip, resource_type="session", resource_id=session_id,
               detail={"question_count": session.total_questions, "provider": session.provider})
    analytics.processing_started(session_id, session.total_questions, session.provider)

    background_tasks.add_task(run_answer_engine, session_id)

    return {"status": "processing", "total": session.total_questions}


def run_answer_engine(session_id: str):
    """Synchronous worker — runs in FastAPI's thread pool. Answers questions in parallel."""
    session = sessions[session_id]
    error_count = 0
    needs_review_count = 0

    # Build doc context once for all questions (not per-question)
    doc_context = build_doc_context(session.docs)

    def process_one(question):
        return question, answer_question(
            question, session.docs, provider=session.provider, doc_context=doc_context
        )

    try:
        with ThreadPoolExecutor(max_workers=ANSWER_CONCURRENCY) as executor:
            futures = {executor.submit(process_one, q): q for q in session.questions}
            for future in as_completed(futures):
                question = futures[future]
                try:
                    _, answer = future.result()
                    session.answers[question.id] = answer
                    if answer.needs_review:
                        needs_review_count += 1
                    def _on_save_done(fut, qid=question.id):
                        exc = fut.exception()
                        if exc:
                            logger.error("db_save_failed", extra={
                                "session_id": session_id, "question_id": qid, "error": str(exc)
                            })
                    _db_save_executor.submit(database.save_answer, session_id, answer).add_done_callback(_on_save_done)
                except Exception as e:
                    error_count += 1
                    logger.error("answer_generation_failed", extra={
                        "session_id": session_id,
                        "question_id": question.id,
                        "error": str(e),
                    })
                    session.answers[question.id] = Answer(
                        question_id=question.id,
                        question_text=question.text,
                        draft_answer="This question requires vendor review. Please provide your response based on your actual security practices.",
                        evidence_coverage=EvidenceCoverage.none,
                        coverage_reason="System error during generation",
                        ai_certainty=0,
                        certainty_reason=str(e),
                        evidence_sources=[],
                        answer_tone=AnswerTone.hedged,
                        needs_review=True,
                        status=AnswerStatus.draft,
                    )
                finally:
                    session.processed_count += 1
                    if QUESTION_DELAY_S > 0:
                        time.sleep(QUESTION_DELAY_S)
    finally:
        session.processing = False
        duration_ms = int((time.time() - (session.processing_started_at or time.time())) * 1000)

        database.mark_processing_complete(session_id)
        audit.emit("processing.complete", resource_type="session", resource_id=session_id,
                   detail={"question_count": session.total_questions, "error_count": error_count,
                           "needs_review_count": needs_review_count, "duration_ms": duration_ms,
                           "provider": session.provider})
        analytics.processing_completed(
            session_id, session.total_questions, session.provider,
            duration_ms, needs_review_count, error_count,
        )


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

@app.get(
    "/api/sessions/{session_id}/status",
    tags=["answers"],
    summary="Poll processing progress",
)
def get_status(session_id: str):
    """Returns current processing state. Poll until `processing: false`."""
    session = get_session(session_id)
    return {
        "processing": session.processing,
        "processed": session.processed_count,
        "total": session.total_questions,
    }


@app.get(
    "/api/sessions/{session_id}/stream",
    tags=["answers"],
    summary="Stream answers via Server-Sent Events as they complete",
)
async def stream_answers(session_id: str):
    """
    Server-Sent Events endpoint. Emits each answer as JSON as it completes during processing.
    Sends `data: [DONE]` when all answers are ready.
    """
    session = get_session(session_id)

    async def event_generator():
        seen: set = set()
        # Wait up to 30s for processing to actually start before giving up
        waited = 0.0
        while not session.processing and session.total_questions == 0:
            await asyncio.sleep(0.5)
            waited += 0.5
            if waited >= 30:
                yield "data: [DONE]\n\n"
                return

        while True:
            # Snapshot the dict to avoid RuntimeError on concurrent resize
            try:
                snapshot = dict(session.answers)
            except RuntimeError:
                snapshot = {}
            for qid, answer in snapshot.items():
                if qid not in seen:
                    seen.add(qid)
                    yield f"data: {json.dumps(answer.model_dump())}\n\n"
            if not session.processing and session.total_questions > 0 and len(seen) >= session.total_questions:
                yield "data: [DONE]\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get(
    "/api/sessions/{session_id}/answers",
    tags=["answers"],
    summary="Get all questions and AI-generated answers",
)
def get_answers(session_id: str):
    """Returns the full question list with their draft answers, coverage scores, and review flags."""
    session = get_session(session_id)
    return {
        "questions": [q.model_dump() for q in session.questions],
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
    }


@app.patch(
    "/api/sessions/{session_id}/answers/{question_id}",
    tags=["answers"],
    summary="Edit or approve an answer",
)
def update_answer(session_id: str, question_id: str, update: dict, request: Request = None):
    """
    Accepts `draft_answer` (string) and/or `status` (draft | edited | approved).
    Editing a draft answer automatically transitions status to `edited`.

    All changes are audit-logged.
    """
    session = get_session(session_id)
    ip = request.client.host if request and request.client else session.client_ip
    answer = session.answers.get(question_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    changes = {}
    if "draft_answer" in update:
        answer.draft_answer = update["draft_answer"]
        if answer.status == AnswerStatus.draft:
            answer.status = AnswerStatus.edited
        changes["draft_answer"] = True
        analytics.answer_edited(session_id, question_id)

    if "status" in update:
        try:
            answer.status = AnswerStatus(update["status"])
            changes["status"] = update["status"]
            analytics.answer_status_changed(session_id, question_id, update["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update['status']}")

    session.answers[question_id] = answer
    database.save_answer(session_id, answer)
    audit.emit("answer.update", actor=ip, resource_type="answer", resource_id=question_id,
               detail={"session_id": session_id, "changes": changes})

    return answer.model_dump()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@app.get(
    "/api/sessions/{session_id}/export/excel",
    tags=["export"],
    summary="Download filled questionnaire as Excel",
)
def download_excel(session_id: str, request: Request = None):
    """Returns an .xlsx file with all questions and approved/edited answers."""
    session = get_session(session_id)
    data = export_excel(session.questions, session.answers)
    analytics.export_downloaded(session_id, "excel", len(session.questions))
    audit.emit("export.download", resource_type="session", resource_id=session_id,
               detail={"format": "excel", "question_count": len(session.questions)})
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=security_questionnaire_response.xlsx"},
    )


@app.get(
    "/api/sessions/{session_id}/export/pdf",
    tags=["export"],
    summary="Download filled questionnaire as PDF",
)
def download_pdf(session_id: str, request: Request = None):
    """Returns a PDF with all questions and approved/edited answers."""
    session = get_session(session_id)
    data = export_pdf(session.questions, session.answers)
    analytics.export_downloaded(session_id, "pdf", len(session.questions))
    audit.emit("export.download", resource_type="session", resource_id=session_id,
               detail={"format": "pdf", "question_count": len(session.questions)})
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=security_questionnaire_response.pdf"},
    )


# ---------------------------------------------------------------------------
# Audit trail (read-only endpoint)
# ---------------------------------------------------------------------------

@app.get(
    "/api/audit",
    tags=["audit"],
    summary="Read recent audit log entries",
)
def read_audit_log(limit: int = 100):
    """
    Returns the last `limit` lines from the audit log.
    In production, restrict this endpoint behind authentication.

    SOC 2 CC7.2 — provides auditable record of all system actions.
    """
    from pathlib import Path
    log_path = Path(os.getenv("AUDIT_LOG_PATH", "audit.log"))
    if not log_path.exists():
        return {"entries": []}
    import json as _json
    lines = log_path.read_text().strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(_json.loads(line))
        except Exception:
            pass
    return {"entries": entries, "total_on_disk": len(lines)}


@app.get(
    "/api/audit/supabase",
    tags=["audit"],
    summary="Read audit events from Supabase",
)
def read_supabase_audit(limit: int = 100, action: str = None):
    """
    Queries the `audit_events` table in Supabase.
    Optionally filter by `action` (e.g. `session.create`, `answer.update`).
    Returns newest-first.
    """
    db = database.get_client()
    if not db:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    query = db.table("audit_events").select("*").order("ts", desc=True).limit(limit)
    if action:
        query = query.eq("action", action)

    result = query.execute()
    return {"entries": result.data, "count": len(result.data)}


@app.get(
    "/api/sessions/{session_id}/summary",
    tags=["answers"],
    summary="Session summary statistics",
)
def session_summary(session_id: str):
    """
    Returns aggregate stats for a completed session:
    coverage breakdown, certainty distribution, needs-review count.
    Useful for Mixpanel-style dashboards built on the data.
    """
    session = get_session(session_id)
    answers = list(session.answers.values())
    if not answers:
        return {"total": 0}

    from collections import Counter
    coverage = Counter(a.evidence_coverage for a in answers)
    tone = Counter(a.answer_tone for a in answers)
    certainties = [a.ai_certainty for a in answers]

    return {
        "total": len(answers),
        "provider": session.provider,
        "needs_review": sum(1 for a in answers if a.needs_review),
        "approved": sum(1 for a in answers if a.status == AnswerStatus.approved),
        "edited": sum(1 for a in answers if a.status == AnswerStatus.edited),
        "coverage": dict(coverage),
        "tone": dict(tone),
        "certainty_avg": round(sum(certainties) / len(certainties), 1),
        "certainty_min": min(certainties),
        "certainty_max": max(certainties),
    }
