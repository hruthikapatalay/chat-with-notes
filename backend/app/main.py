"""FastAPI application entrypoint for Chat With Your Notes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, documents
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Upload study notes, retrieve relevant chunks, and chat with them.",
    version="0.1.0",
)


# CORS allows the plain HTML frontend to call the API from a local browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a friendly message so you know the API is running."""

    return {
        "app": settings.app_name,
        "message": "FastAPI backend is running.",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Small endpoint used to test that the server can respond."""

    return {"status": "ok"}
