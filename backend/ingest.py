import fitz  # PyMuPDF
from models import ComplianceDoc, DocType, TrustLevel


def extract_pdf_text(filepath: str) -> tuple[str, int]:
    doc = fitz.open(filepath)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages), len(pages)


def detect_doc_type(filename: str) -> tuple[DocType, TrustLevel]:
    lower = filename.lower()
    if "soc" in lower and ("2" in lower or "ii" in lower):
        return DocType.soc2, TrustLevel.high
    elif "iso" in lower and "27001" in lower:
        return DocType.iso27001, TrustLevel.high
    else:
        return DocType.policy, TrustLevel.medium


def ingest_pdf(filepath: str, filename: str) -> ComplianceDoc:
    text, pages = extract_pdf_text(filepath)
    doc_type, trust_level = detect_doc_type(filename)
    return ComplianceDoc(
        filename=filename,
        doc_type=doc_type,
        trust_level=trust_level,
        text=text,
        pages=pages,
    )


def extract_docx_text(filepath: str) -> tuple[str, int]:
    from docx import Document
    doc = Document(filepath)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    approx_pages = max(1, len(" ".join(paragraphs)) // 2500)
    return "\n\n".join(paragraphs), approx_pages


def ingest_docx(filepath: str, filename: str) -> ComplianceDoc:
    text, pages = extract_docx_text(filepath)
    doc_type, trust_level = detect_doc_type(filename)
    return ComplianceDoc(filename=filename, doc_type=doc_type, trust_level=trust_level, text=text, pages=pages)


def ingest_manual(text: str) -> ComplianceDoc:
    return ComplianceDoc(
        filename="Manual Input",
        doc_type=DocType.manual,
        trust_level=TrustLevel.medium,
        text=text,
        pages=1,
    )
