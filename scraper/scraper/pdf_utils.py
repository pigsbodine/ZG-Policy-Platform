"""PDF text extraction using pdfminer.six."""
import io
import logging

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract plain text from raw PDF bytes.

    Returns an empty string if extraction fails or produces no text.
    Silently ignores encrypted/corrupted PDFs rather than raising.
    """
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        from pdfminer.pdfpage import PDFPage
        from pdfminer.pdfdocument import PDFEncryptionError
    except ImportError:
        logger.error("pdfminer.six is not installed; cannot extract PDF text")
        return ""

    try:
        output = io.StringIO()
        extract_text_to_fp(
            io.BytesIO(pdf_bytes),
            output,
            laparams=LAParams(),
            output_type="text",
            codec="utf-8",
        )
        text = output.getvalue()
        # Collapse excessive blank lines that pdfminer tends to produce
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as exc:
        logger.warning("PDF extraction failed: %s", exc)
        return ""


def looks_like_pdf(url: str, content_type: str) -> bool:
    """Return True if the URL or Content-Type indicates a PDF response."""
    import re
    if "application/pdf" in content_type.lower():
        return True
    # Some servers serve PDFs with wrong content-type; fall back to URL
    return bool(re.search(r"\.pdf(\?|#|$)", url, re.IGNORECASE))
