"""
Tests for backend/ingest.py

Covers:
- detect_doc_type — SOC 2 detection (various filename patterns)
- detect_doc_type — ISO 27001 detection
- detect_doc_type — fallback to policy/medium
- ingest_manual — returns correct ComplianceDoc fields
- ingest_pdf — wires extract_pdf_text + detect_doc_type correctly
- extract_pdf_text — calls PyMuPDF and returns (text, page_count)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ComplianceDoc, DocType, TrustLevel  # noqa: E402
from ingest import detect_doc_type, extract_pdf_text, ingest_manual, ingest_pdf  # noqa: E402


# ---------------------------------------------------------------------------
# detect_doc_type
# ---------------------------------------------------------------------------

class TestDetectDocType:
    # SOC 2 variants
    @pytest.mark.parametrize("filename", [
        "SOC2_2024.pdf",
        "soc2_report.pdf",
        "VendorSOC2TypeII.pdf",
        "AuditSOCII.pdf",
        "soc_2_type_ii.pdf",
    ])
    def test_soc2_detected(self, filename):
        doc_type, trust = detect_doc_type(filename)
        assert doc_type == DocType.soc2
        assert trust == TrustLevel.high

    # ISO 27001 variants
    @pytest.mark.parametrize("filename", [
        "ISO27001_Certificate.pdf",
        "iso_27001_2022.pdf",
        "CompanyISO27001Cert.pdf",
    ])
    def test_iso27001_detected(self, filename):
        doc_type, trust = detect_doc_type(filename)
        assert doc_type == DocType.iso27001
        assert trust == TrustLevel.high

    # Fallback to policy
    @pytest.mark.parametrize("filename", [
        "security_policy.pdf",
        "data_retention.pdf",
        "GDPR_compliance.pdf",
        "random_document.txt",
        "SOC_without_number.pdf",  # "soc" present but no "2" or "ii"
    ])
    def test_policy_fallback(self, filename):
        doc_type, trust = detect_doc_type(filename)
        assert doc_type == DocType.policy
        assert trust == TrustLevel.medium

    def test_case_insensitive(self):
        """Filename matching must be case-insensitive."""
        doc_type, _ = detect_doc_type("SOC2_REPORT.PDF")
        assert doc_type == DocType.soc2

    def test_returns_tuple(self):
        result = detect_doc_type("some_policy.pdf")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# ingest_manual
# ---------------------------------------------------------------------------

class TestIngestManual:
    def test_returns_compliance_doc(self):
        result = ingest_manual("We have AES-256 encryption at rest.")
        assert isinstance(result, ComplianceDoc)

    def test_filename_is_manual_input(self):
        result = ingest_manual("Some text")
        assert result.filename == "Manual Input"

    def test_doc_type_is_manual(self):
        result = ingest_manual("Some text")
        assert result.doc_type == DocType.manual

    def test_trust_level_is_medium(self):
        result = ingest_manual("Some text")
        assert result.trust_level == TrustLevel.medium

    def test_text_is_preserved(self):
        text = "We encrypt all data using AES-256."
        result = ingest_manual(text)
        assert result.text == text

    def test_pages_is_one(self):
        result = ingest_manual("Any text")
        assert result.pages == 1

    def test_empty_string_handled(self):
        result = ingest_manual("")
        assert result.text == ""
        assert result.pages == 1

    def test_long_text_preserved(self):
        long_text = "Security policy text. " * 1000
        result = ingest_manual(long_text)
        assert result.text == long_text


# ---------------------------------------------------------------------------
# extract_pdf_text
# ---------------------------------------------------------------------------

class TestExtractPdfText:
    def _make_fitz_doc(self, page_texts):
        pages = []
        for text in page_texts:
            page = MagicMock()
            page.get_text.return_value = text
            pages.append(page)

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter(pages))
        mock_doc.close = MagicMock()
        return mock_doc

    def test_returns_text_and_page_count(self):
        mock_doc = self._make_fitz_doc(["Page 1 text", "Page 2 text"])
        with patch("ingest.fitz.open", return_value=mock_doc):
            text, pages = extract_pdf_text("/fake/path.pdf")
        assert pages == 2

    def test_pages_joined_with_double_newline(self):
        mock_doc = self._make_fitz_doc(["Page 1", "Page 2"])
        with patch("ingest.fitz.open", return_value=mock_doc):
            text, _ = extract_pdf_text("/fake/path.pdf")
        assert "Page 1\n\nPage 2" == text

    def test_single_page_doc(self):
        mock_doc = self._make_fitz_doc(["Only page"])
        with patch("ingest.fitz.open", return_value=mock_doc):
            text, pages = extract_pdf_text("/fake/path.pdf")
        assert pages == 1
        assert "Only page" in text

    def test_fitz_close_called(self):
        mock_doc = self._make_fitz_doc(["text"])
        with patch("ingest.fitz.open", return_value=mock_doc):
            extract_pdf_text("/fake/path.pdf")
        mock_doc.close.assert_called_once()


# ---------------------------------------------------------------------------
# ingest_pdf
# ---------------------------------------------------------------------------

class TestIngestPdf:
    def _patch_extract(self, text="PDF content", pages=5):
        return patch("ingest.extract_pdf_text", return_value=(text, pages))

    def test_returns_compliance_doc(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/soc2.pdf", "SOC2_2024.pdf")
        assert isinstance(result, ComplianceDoc)

    def test_filename_set_correctly(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/soc2.pdf", "SOC2_2024.pdf")
        assert result.filename == "SOC2_2024.pdf"

    def test_doc_type_detected_as_soc2(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/soc2.pdf", "SOC2_2024.pdf")
        assert result.doc_type == DocType.soc2

    def test_doc_type_detected_as_iso27001(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/iso.pdf", "ISO27001_Certificate.pdf")
        assert result.doc_type == DocType.iso27001

    def test_doc_type_detected_as_policy(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/policy.pdf", "data_retention_policy.pdf")
        assert result.doc_type == DocType.policy

    def test_trust_level_high_for_soc2(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/soc2.pdf", "SOC2_2024.pdf")
        assert result.trust_level == TrustLevel.high

    def test_trust_level_medium_for_policy(self):
        with self._patch_extract():
            result = ingest_pdf("/fake/policy.pdf", "security_policy.pdf")
        assert result.trust_level == TrustLevel.medium

    def test_text_and_pages_from_extract(self):
        with self._patch_extract(text="Extracted text here.", pages=12):
            result = ingest_pdf("/fake/doc.pdf", "SOC2_2024.pdf")
        assert result.text == "Extracted text here."
        assert result.pages == 12
