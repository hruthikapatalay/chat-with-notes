"""PDF text extraction and OCR fallback logic."""
 
from __future__ import annotations
 
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, TYPE_CHECKING
 
import fitz
 
if TYPE_CHECKING:
    from paddleocr import PaddleOCR
 
 
SCANNED_TEXT_THRESHOLD = 30
 
_ocr_model: "PaddleOCR | None" = None
 
 
def get_ocr_model() -> "PaddleOCR":
    """Load PaddleOCR once and reuse it across uploads.
 
    OCR models are large, so creating a new model for every page would be slow.
    This small cache keeps the first upload slower and later uploads faster.
 
    Raises RuntimeError if paddleocr isn't installed in this environment
    (e.g. on hosts where paddlepaddle has no compatible build), so callers
    can catch it and degrade gracefully instead of crashing the app.
    """
 
    global _ocr_model
    if _ocr_model is None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed in this environment. "
                "Scanned/image-based PDF pages cannot be OCR'd here."
            ) from exc
 
        _ocr_model = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    return _ocr_model
 
 
def _extract_text_from_ocr_result(result: Any) -> str:
    """Convert PaddleOCR's nested result format into a single text string."""
 
    text_parts: list[str] = []
 
    if not result:
        return ""
 
    for page_result in result:
        if isinstance(page_result, dict):
            rec_texts = page_result.get("rec_texts", [])
            text_parts.extend(str(text) for text in rec_texts if text)
            continue
 
        if isinstance(page_result, list):
            for line in page_result:
                if isinstance(line, list) and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, tuple | list) and text_info:
                        text_parts.append(str(text_info[0]))
 
    return "\n".join(text_parts).strip()
 
 
def _ocr_page(page: fitz.Page, tmp_dir: Path) -> str:
    """Render one PDF page to an image and run PaddleOCR on that image.
 
    Returns a placeholder string if OCR is unavailable in this environment,
    instead of raising and crashing the upload.
    """
 
    image_path = tmp_dir / f"page-{page.number + 1}.png"
 
    # 2x zoom gives OCR more pixels to read, which helps scanned pages.
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pixmap.save(image_path)
 
    try:
        model = get_ocr_model()
    except RuntimeError:
        return "[OCR unavailable in this environment]"
 
    result = model.ocr(str(image_path))
    return _extract_text_from_ocr_result(result)
 
 
def extract_pdf_pages(pdf_path: Path) -> tuple[list[dict[str, Any]], int]:
    """Extract text from every page of a PDF.
 
    PyMuPDF handles normal digital PDFs. If a page has almost no extractable
    text, we treat it as scanned/image-based and run OCR for that page.
    """
 
    pages: list[dict[str, Any]] = []
 
    with fitz.open(pdf_path) as document, TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
 
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            extraction_method = "pymupdf"
 
            if len(text) < SCANNED_TEXT_THRESHOLD:
                text = _ocr_page(page, tmp_dir)
                extraction_method = (
                    "ocr_unavailable" if "[OCR unavailable" in text else "paddleocr"
                )
 
            pages.append(
                {
                    "page_number": page_index,
                    "text": text.strip(),
                    "extraction_method": extraction_method,
                }
            )
 
        return pages, document.page_count
 
