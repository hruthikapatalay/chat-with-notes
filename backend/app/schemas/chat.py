"""Chat request and response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for asking a question about uploaded notes."""

    question: str = Field(min_length=1)
    session_id: str = "default"
    top_k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    """A retrieved note chunk used to answer the question."""

    document_id: int
    filename: str
    page_number: int
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    """Answer returned by the RAG chat endpoint."""

    answer: str
    sources: list[Source]
