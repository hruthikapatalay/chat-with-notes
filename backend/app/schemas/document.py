"""Document upload response schemas."""

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response returned after a PDF is uploaded and indexed."""

    document_id: int
    filename: str
    page_count: int
    chunk_count: int
    message: str
