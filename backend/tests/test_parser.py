"""
Tests for backend/parser.py

Covers:
- extract_questions_with_claude happy path
- extract_questions_with_claude with markdown-fenced response
- extract_questions_with_claude with invalid JSON raises ValueError
- parse_text_questionnaire delegates to extract_questions_with_claude
- parse_excel_questionnaire — detects question column, skips empty rows
- parse_excel_questionnaire — falls back to longest-avg-string column
- parse_excel_questionnaire — raises when no object columns found
- parse_pdf_questionnaire — calls fitz and extract_questions_with_claude
- answer_format mapping (valid + invalid fallback to freeform)
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import AnswerFormat, Question  # noqa: E402
import parser as p  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GOOD_ARRAY = json.dumps([
    {"number": "1", "question_text": "Do you encrypt data at rest?", "answer_format": "yes_no_evidence"},
    {"number": "2", "question_text": "Describe your patch management.", "answer_format": "freeform"},
])


# ---------------------------------------------------------------------------
# extract_questions_with_claude
# ---------------------------------------------------------------------------

class TestExtractQuestionsWithClaude:
    def test_returns_list_of_questions(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("Sample questionnaire text")
        assert isinstance(result, list)
        assert all(isinstance(q, Question) for q in result)

    def test_correct_question_count(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert len(result) == 2

    def test_question_text_extracted(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert result[0].text == "Do you encrypt data at rest?"
        assert result[1].text == "Describe your patch management."

    def test_question_ids_sequential(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert result[0].id == "q_001"
        assert result[1].id == "q_002"

    def test_answer_format_yes_no_evidence(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert result[0].answer_format == AnswerFormat.yes_no_evidence

    def test_answer_format_freeform(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert result[1].answer_format == AnswerFormat.freeform

    def test_invalid_answer_format_falls_back_to_freeform(self):
        bad_format = json.dumps([
            {"number": "1", "question_text": "A question?", "answer_format": "not_a_real_format"},
        ])
        with patch("parser.chat", return_value=bad_format):
            result = p.extract_questions_with_claude("text")
        assert result[0].answer_format == AnswerFormat.freeform

    def test_all_answer_formats_mapped(self):
        """Every valid AnswerFormat should be preserved from the LLM response."""
        formats = ["yes_no", "yes_no_evidence", "freeform", "select", "numeric"]
        items = [
            {"number": str(i+1), "question_text": f"Q{i+1}?", "answer_format": fmt}
            for i, fmt in enumerate(formats)
        ]
        with patch("parser.chat", return_value=json.dumps(items)):
            result = p.extract_questions_with_claude("text")
        for q, fmt in zip(result, formats):
            assert q.answer_format == AnswerFormat(fmt)

    def test_markdown_fenced_response_is_handled(self):
        """The parser should strip markdown fences before parsing JSON."""
        fenced = f"```json\n{GOOD_ARRAY}\n```"
        with patch("parser.chat", return_value=fenced):
            result = p.extract_questions_with_claude("text")
        assert len(result) == 2

    def test_invalid_json_raises_value_error(self):
        """Completely unparseable LLM output should raise ValueError."""
        with patch("parser.chat", return_value="not json at all no array either"):
            with pytest.raises(ValueError, match="Could not parse questions"):
                p.extract_questions_with_claude("text")

    def test_provider_forwarded_to_chat(self):
        """The provider kwarg should be passed through to chat()."""
        with patch("parser.chat", return_value=GOOD_ARRAY) as mock_chat:
            p.extract_questions_with_claude("text", provider="groq")
        _, kwargs = mock_chat.call_args
        assert kwargs.get("provider") == "groq"

    def test_text_truncated_to_10000_chars_in_prompt(self):
        """Long questionnaire text should be truncated in the LLM user prompt."""
        long_text = "Q? " * 5000  # >> 10 000 chars
        with patch("parser.chat", return_value=GOOD_ARRAY) as mock_chat:
            p.extract_questions_with_claude(long_text)
        user_prompt = mock_chat.call_args.kwargs.get("user") or mock_chat.call_args[0][1]
        # The prompt uses text[:10000] so the raw long_text should not appear verbatim
        assert long_text not in user_prompt

    def test_original_row_set_correctly(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.extract_questions_with_claude("text")
        assert result[0].original_row == 0
        assert result[1].original_row == 1


# ---------------------------------------------------------------------------
# parse_text_questionnaire
# ---------------------------------------------------------------------------

class TestParseTextQuestionnaire:
    def test_delegates_to_extract_questions(self):
        with patch("parser.extract_questions_with_claude", return_value=[]) as mock_extract:
            p.parse_text_questionnaire("some text", provider="groq")
        mock_extract.assert_called_once_with("some text", provider="groq")

    def test_returns_list(self):
        with patch("parser.chat", return_value=GOOD_ARRAY):
            result = p.parse_text_questionnaire("sample questionnaire text")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# parse_excel_questionnaire
# ---------------------------------------------------------------------------

class TestParseExcelQuestionnaire:
    def _make_df(self, data: dict):
        import pandas as pd
        return pd.DataFrame(data)

    def test_detects_question_column_by_name(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({
            "Question": ["Do you encrypt?", "Do you use MFA?", ""],
            "Answer": ["", "", ""],
        })
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert len(result) == 2
        assert result[0].text == "Do you encrypt?"

    def test_skips_empty_and_nan_rows(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({
            "Question": ["Q1?", "", None, "Q4?"],
        })
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert len(result) == 2
        assert all(q.text for q in result)

    def test_sequential_ids_assigned(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"Question": ["Q1?", "Q2?", "Q3?"]})
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert result[0].id == "q_001"
        assert result[1].id == "q_002"
        assert result[2].id == "q_003"

    def test_all_questions_default_to_freeform(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"Question": ["Q1?", "Q2?"]})
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert all(q.answer_format == AnswerFormat.freeform for q in result)

    def test_falls_back_to_longest_avg_string_column(self, tmp_path):
        """When no 'question/requirement/control/item' column exists,
        falls back to the object column with longest average string length."""
        import pandas as pd
        df = pd.DataFrame({
            "col_a": ["Hi", "Hello world and more text here"],
            "col_b": ["A", "B"],
        })
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        # Both rows from col_a should be used (longest avg)
        texts = [q.text for q in result]
        assert "Hi" in texts or "Hello world and more text here" in texts

    def test_raises_when_no_object_columns(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"num_col": [1, 2, 3]})
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        with pytest.raises(ValueError, match="Could not detect question column"):
            p.parse_excel_questionnaire(filepath)

    def test_recognises_requirement_column_name(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"Requirement": ["Encrypt at rest", "Use MFA"]})
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert len(result) == 2

    def test_original_row_index_preserved(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"Question": ["Q1?", "Q2?"]})
        filepath = str(tmp_path / "test.xlsx")
        df.to_excel(filepath, index=False)

        result = p.parse_excel_questionnaire(filepath)
        assert result[0].original_row == 0
        assert result[1].original_row == 1


# ---------------------------------------------------------------------------
# parse_pdf_questionnaire
# ---------------------------------------------------------------------------

class TestParsePdfQuestionnaire:
    def test_calls_fitz_open(self):
        """parse_pdf_questionnaire should open the file with PyMuPDF."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Q1. Do you encrypt?"
        mock_fitz_doc = MagicMock()
        mock_fitz_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_fitz_doc.close = MagicMock()

        with patch("parser.fitz.open", return_value=mock_fitz_doc):
            with patch("parser.extract_questions_with_claude", return_value=[]) as mock_extract:
                p.parse_pdf_questionnaire("/fake/path.pdf", provider="groq")

        mock_extract.assert_called_once()
        text_arg = mock_extract.call_args[0][0]
        assert "Q1. Do you encrypt?" in text_arg

    def test_provider_forwarded(self):
        mock_page = MagicMock()
        mock_page.get_text.return_value = "text"
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.close = MagicMock()

        with patch("parser.fitz.open", return_value=mock_doc):
            with patch("parser.extract_questions_with_claude", return_value=[]) as mock_extract:
                p.parse_pdf_questionnaire("/fake/path.pdf", provider="anthropic")

        _, kwargs = mock_extract.call_args
        assert kwargs.get("provider") == "anthropic"
