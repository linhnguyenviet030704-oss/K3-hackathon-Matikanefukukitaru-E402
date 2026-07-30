"""
rag/chunker.py — Split cleaned documents into overlapping chunks with metadata.

Uses LangChain's RecursiveCharacterTextSplitter.
Each chunk is returned as a LangChain Document with a rich metadata dict.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from rag.config import cfg
from rag.loaders import RawDocument

logger = logging.getLogger(__name__)


# ── ICD-10 auto-detection ─────────────────────────────────────────────────────

def _detect_disease_and_icd(text: str, source_file: str) -> tuple[str, str]:
    """
    Heuristically detect the primary disease category and ICD-10 code
    from a chunk's text content or source filename.

    Returns:
        (disease_category, icd_code) — both default to "" if not detected.
    """
    combined = (text + " " + source_file).lower()
    for keyword, icd in cfg.DISEASE_ICD_MAP.items():
        if keyword in combined:
            # Capitalise the matched keyword for display
            disease = keyword.title()
            return disease, icd
    return "", ""


# ── Chunker ───────────────────────────────────────────────────────────────────

class DocumentChunker:
    """
    Split a RawDocument into overlapping text chunks and attach metadata.

    Args:
        chunk_size:    Maximum number of characters per chunk.
        chunk_overlap: Number of characters to overlap between consecutive chunks.
    """

    def __init__(
        self,
        chunk_size: int = cfg.CHUNK_SIZE,
        chunk_overlap: int = cfg.CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )

    def chunk(self, raw_doc: RawDocument) -> list[Document]:
        """
        Split *raw_doc* into Document objects with full metadata.

        Args:
            raw_doc: A cleaned RawDocument.

        Returns:
            List of LangChain Document objects.
        """
        if not raw_doc.text.strip():
            logger.warning("Skipping empty document: %s", raw_doc.source_file)
            return []

        text_chunks: list[str] = self._splitter.split_text(raw_doc.text)
        today = date.today().isoformat()
        documents: list[Document] = []

        for idx, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue

            disease_cat, icd_code = _detect_disease_and_icd(
                chunk_text, raw_doc.source_file
            )

            metadata: dict[str, Any] = {
                "chunk_id": str(uuid.uuid4()),
                "source_file": raw_doc.source_file,
                "source_type": raw_doc.source_type,
                "file_format": raw_doc.file_format,
                "disease_category": disease_cat,
                "icd_code": icd_code,
                "chunk_index": idx,
                "total_chunks": len(text_chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "language": _detect_language(chunk_text),
                "created_at": today,
            }

            # Optional: carry over any extra metadata from the raw doc
            metadata.update(raw_doc.extra)

            documents.append(Document(page_content=chunk_text, metadata=metadata))

        logger.info(
            "Chunked '%s' → %d chunks (chunk_size=%d, overlap=%d)",
            raw_doc.source_file,
            len(documents),
            self.chunk_size,
            self.chunk_overlap,
        )
        return documents

    def chunk_all(self, raw_docs: list[RawDocument]) -> list[Document]:
        """Chunk a list of raw documents, returning a flat list of Document objects."""
        all_docs: list[Document] = []
        for raw_doc in raw_docs:
            all_docs.extend(self.chunk(raw_doc))
        logger.info("Total chunks produced: %d", len(all_docs))
        return all_docs


# ── Language detection (lightweight heuristic) ────────────────────────────────

_VI_CHARS = set("àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")


def _detect_language(text: str) -> str:
    """
    Heuristic language detection — returns 'vi' or 'en'.
    Vietnamese is detected by the presence of diacritic characters.
    """
    sample = text[:300].lower()
    vi_count = sum(1 for ch in sample if ch in _VI_CHARS)
    return "vi" if vi_count > 5 else "en"
