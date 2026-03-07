from __future__ import annotations

import json
import re
from typing import List

import fitz  # PyMuPDF
import pandas as pd

from llm import chat

from models import AnswerFormat, Question


def extract_questions_with_claude(text: str, provider: str | None = None) -> List[Question]:
    system = "You are a security questionnaire parser. Return only valid JSON — no markdown fences, no preamble."
    user = f"""Extract all questions from this security questionnaire text.

Return a JSON array only — no markdown, no explanation, just the array.

Each item must have:
- "number": question number or identifier as a string
- "question_text": the full question text
- "answer_format": one of "yes_no", "yes_no_evidence", "freeform", "select", "numeric"

Rules for answer_format:
- "yes_no": simple yes/no with no follow-up
- "yes_no_evidence": yes/no + asks for description or details
- "freeform": open-ended description
- "select": multiple choice or frequency options
- "numeric": asks for a number, date, or count

TEXT:
{text[:10000]}

Return ONLY a valid JSON array. Start your response with [ and end with ]."""

    content = chat(system=system, user=user, max_tokens=4096, provider=provider)

    # Strip markdown code fences if present
    if "```" in content:
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            content = match.group()

    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract any JSON array
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            items = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse questions from Claude response: {content[:200]}")

    questions = []
    for i, item in enumerate(items):
        raw_format = item.get("answer_format", "freeform")
        try:
            fmt = AnswerFormat(raw_format)
        except ValueError:
            fmt = AnswerFormat.freeform

        questions.append(
            Question(
                id=f"q_{i + 1:03d}",
                text=item.get("question_text", item.get("text", "")).strip(),
                answer_format=fmt,
                original_row=i,
            )
        )

    return questions


def parse_pdf_questionnaire(filepath: str, provider: str | None = None) -> List[Question]:
    doc = fitz.open(filepath)
    text = "\n\n".join(page.get_text() for page in doc)
    doc.close()
    return extract_questions_with_claude(text, provider=provider)


def parse_excel_questionnaire(filepath: str) -> List[Question]:
    df = pd.read_excel(filepath)

    # Auto-detect the question column
    question_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in ["question", "requirement", "control", "item"]):
            question_col = col
            break

    if question_col is None:
        # Fall back to column with longest average string length
        str_cols = df.select_dtypes(include="object").columns
        if len(str_cols) == 0:
            raise ValueError("Could not detect question column in spreadsheet")
        question_col = max(str_cols, key=lambda c: df[c].astype(str).str.len().mean())

    questions = []
    for i, row in df.iterrows():
        text = str(row[question_col]).strip()
        if not text or text.lower() == "nan":
            continue
        questions.append(
            Question(
                id=f"q_{len(questions) + 1:03d}",
                text=text,
                answer_format=AnswerFormat.freeform,
                original_row=int(i),
            )
        )

    return questions


def parse_text_questionnaire(text: str, provider: str | None = None) -> List[Question]:
    return extract_questions_with_claude(text, provider=provider)
