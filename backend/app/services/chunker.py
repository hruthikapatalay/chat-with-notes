"""Text chunking logic using RecursiveCharacterTextSplitter."""

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split extracted page text into retrieval-friendly chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks: list[dict[str, Any]] = []

    for page in pages:
        page_text = page["text"]
        if not page_text:
            continue

        page_chunks = splitter.split_text(page_text)
        for chunk_index, chunk_text in enumerate(page_chunks):
            chunks.append(
                {
                    "text": chunk_text,
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index,
                    "extraction_method": page["extraction_method"],
                }
            )

    return chunks
