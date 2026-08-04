"""PDF upload and ingestion routes."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentUploadResponse
from app.services.chunker import chunk_pages
from app.services.embeddings import embed_texts
from app.services.pdf_extractor import extract_pdf_pages
from app.vector_store.faiss_store import add_chunks_to_user_index


router = APIRouter(prefix="/documents", tags=["documents"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_ROOT = PROJECT_ROOT / "data" / "uploads"


def _safe_filename(filename: str) -> str:
    """Return a filesystem-safe version of an uploaded filename."""

    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    return cleaned or "uploaded.pdf"


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a PDF, extract text, chunk it, embed it, and save it to FAISS."""

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    safe_name = _safe_filename(file.filename or "uploaded.pdf")
    user_upload_dir = UPLOAD_ROOT / f"user_{current_user.id}"
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    stored_path = user_upload_dir / safe_name
    stored_path.write_bytes(await file.read())

    document = Document(
        user_id=current_user.id,
        filename=safe_name,
        stored_path=str(stored_path),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        pages, page_count = extract_pdf_pages(stored_path)
        chunks = chunk_pages(pages)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text was found in this PDF.",
            )

        embeddings = embed_texts([chunk["text"] for chunk in chunks])
        chunk_count = add_chunks_to_user_index(
            user_id=current_user.id,
            embeddings=embeddings,
            chunks=chunks,
            document_id=document.id,
            filename=safe_name,
        )

        document.page_count = page_count
        document.chunk_count = chunk_count
        db.commit()
        db.refresh(document)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {exc}",
        ) from exc

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        chunk_count=document.chunk_count,
        message="PDF uploaded and indexed successfully.",
    )
