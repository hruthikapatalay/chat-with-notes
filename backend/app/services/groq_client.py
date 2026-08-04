"""Groq OpenAI-compatible API client."""

import httpx

from app.core.config import get_settings


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def generate_answer(question: str, context: str) -> str:
    """Ask Groq to answer a question using retrieved note context."""

    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing from your .env file.")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful study assistant. Answer only using the "
                "provided context. If the context does not contain the answer, "
                "say that the notes do not provide enough information."
            ),
        },
        {
            "role": "user",
            "content": (
                "Context from the user's uploaded notes:\n\n"
                f"{context}\n\n"
                f"Question: {question}"
            ),
        },
    ]

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    response = httpx.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
