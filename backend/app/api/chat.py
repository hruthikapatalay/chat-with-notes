"""Question-answering chat routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, Source
from app.services.embeddings import embed_texts
from app.services.groq_client import generate_answer
from app.vector_store.faiss_store import search_user_index


router = APIRouter(prefix="/chat", tags=["chat"])


def _build_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context block for the LLM."""

    context_parts = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            (
                f"[Source {index}: {chunk['filename']}, "
                f"page {chunk['page_number']}]\n"
                f"{chunk['text']}"
            )
        )

    return "\n\n---\n\n".join(context_parts)


def _build_sources(retrieved_chunks: list[dict]) -> list[Source]:
    """Convert retrieved chunk metadata into API response source objects."""

    return [
        Source(
            document_id=chunk["document_id"],
            filename=chunk["filename"],
            page_number=chunk["page_number"],
            chunk_index=chunk["chunk_index"],
            score=chunk["score"],
        )
        for chunk in retrieved_chunks
    ]


@router.post("/query", response_model=ChatResponse)
def query_notes(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Answer a user question using retrieved chunks from their notes."""

    question_embedding = embed_texts([payload.question])
    retrieved_chunks = search_user_index(
        user_id=current_user.id,
        query_embedding=question_embedding[0],
        top_k=payload.top_k,
    )

    if not retrieved_chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No indexed notes found for this user. Upload a PDF first.",
        )

    context = _build_context(retrieved_chunks)
    sources = _build_sources(retrieved_chunks)

    try:
        answer = generate_answer(question=payload.question, context=context)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate answer with Groq: {exc}",
        ) from exc

    chat_message = ChatMessage(
        user_id=current_user.id,
        session_id=payload.session_id,
        question=payload.question,
        answer=answer,
        sources_json=json.dumps([source.model_dump() for source in sources]),
    )
    db.add(chat_message)
    db.commit()

    return ChatResponse(answer=answer, sources=sources)
