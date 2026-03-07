import io
import os
import tempfile
import uuid
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from engine import answer_question
from export import export_excel, export_pdf
from ingest import ingest_manual, ingest_pdf
from models import Answer, AnswerStatus, AnswerTone, EvidenceCoverage
from parser import parse_excel_questionnaire, parse_pdf_questionnaire, parse_text_questionnaire

app = FastAPI(title="Seques — Security Questionnaire Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory session store (MVP — restarts clear all data)
# ---------------------------------------------------------------------------

class Session:
    def __init__(self, session_id: str):
        self.id = session_id
        self.docs = []
        self.questions = []
        self.answers: Dict[str, Answer] = {}
        self.processing = False
        self.processed_count = 0
        self.total_questions = 0
        self.questionnaire_filename: Optional[str] = None
        self.questionnaire_type: Optional[str] = None


sessions: Dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/sessions")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session(session_id)
    return {"session_id": session_id}


@app.post("/api/sessions/{session_id}/docs")
async def upload_docs(session_id: str, files: List[UploadFile] = File(...)):
    session = get_session(session_id)

    added = []
    for file in files:
        suffix = os.path.splitext(file.filename)[1].lower()
        if suffix != ".pdf":
            continue  # Only PDFs for compliance docs in Phase 1

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            doc = ingest_pdf(tmp_path, file.filename)
            session.docs.append(doc)
            added.append({"filename": doc.filename, "doc_type": doc.doc_type, "pages": doc.pages})
        finally:
            os.unlink(tmp_path)

    return {"docs": added}


@app.post("/api/sessions/{session_id}/manual-doc")
async def upload_manual_doc(session_id: str, text: str = Form(...)):
    session = get_session(session_id)
    doc = ingest_manual(text)
    session.docs.append(doc)
    return {"ok": True}


@app.post("/api/sessions/{session_id}/questionnaire")
async def upload_questionnaire(
    session_id: str,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    session = get_session(session_id)

    if file and file.filename:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                questions = parse_pdf_questionnaire(tmp_path)
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
        questions = parse_text_questionnaire(text.strip())
        session.questionnaire_type = "text"

    else:
        raise HTTPException(status_code=400, detail="Provide a file or pasted text")

    session.questions = questions
    session.total_questions = len(questions)

    return {
        "question_count": len(questions),
        "questions": [q.model_dump() for q in questions],
    }


@app.post("/api/sessions/{session_id}/process")
async def process_questionnaire(session_id: str, background_tasks: BackgroundTasks):
    session = get_session(session_id)

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="ANTHROPIC_API_KEY not configured. Copy backend/.env.example to backend/.env and add your key.",
        )
    if not session.docs:
        raise HTTPException(status_code=400, detail="No compliance docs uploaded")
    if not session.questions:
        raise HTTPException(status_code=400, detail="No questionnaire uploaded")

    session.processing = True
    session.processed_count = 0
    session.answers = {}

    background_tasks.add_task(run_answer_engine, session_id)

    return {"status": "processing", "total": session.total_questions}


def run_answer_engine(session_id: str):
    """Runs synchronously in FastAPI's thread pool. Called per-session."""
    session = sessions[session_id]
    try:
        for question in session.questions:
            try:
                answer = answer_question(question, session.docs)
                session.answers[question.id] = answer
            except Exception as e:
                session.answers[question.id] = Answer(
                    question_id=question.id,
                    question_text=question.text,
                    draft_answer=f"Error generating answer: {e}",
                    evidence_coverage=EvidenceCoverage.none,
                    coverage_reason="System error during generation",
                    ai_certainty=0,
                    certainty_reason=str(e),
                    evidence_sources=[],
                    answer_tone=AnswerTone.cannot_answer,
                    needs_review=True,
                    status=AnswerStatus.draft,
                )
            finally:
                session.processed_count += 1
    finally:
        session.processing = False


@app.get("/api/sessions/{session_id}/status")
def get_status(session_id: str):
    session = get_session(session_id)
    return {
        "processing": session.processing,
        "processed": session.processed_count,
        "total": session.total_questions,
    }


@app.get("/api/sessions/{session_id}/answers")
def get_answers(session_id: str):
    session = get_session(session_id)
    return {
        "questions": [q.model_dump() for q in session.questions],
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
    }


@app.patch("/api/sessions/{session_id}/answers/{question_id}")
def update_answer(session_id: str, question_id: str, update: dict):
    session = get_session(session_id)
    answer = session.answers.get(question_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    if "draft_answer" in update:
        answer.draft_answer = update["draft_answer"]
        if answer.status == AnswerStatus.draft:
            answer.status = AnswerStatus.edited

    if "status" in update:
        try:
            answer.status = AnswerStatus(update["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update['status']}")

    session.answers[question_id] = answer
    return answer.model_dump()


@app.get("/api/sessions/{session_id}/export/excel")
def download_excel(session_id: str):
    session = get_session(session_id)
    data = export_excel(session.questions, session.answers)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=security_questionnaire_response.xlsx"},
    )


@app.get("/api/sessions/{session_id}/export/pdf")
def download_pdf(session_id: str):
    session = get_session(session_id)
    data = export_pdf(session.questions, session.answers)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=security_questionnaire_response.pdf"},
    )
