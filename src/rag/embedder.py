"""
rag/embedder.py — Embedding model wrapper.

Wraps HuggingFace sentence-transformers via LangChain so the rest
of the project only depends on this single interface.
The recommended model is BAAI/bge-m3 (multilingual, high performance).
"""

from __future__ import annotations

import logging

from langchain_huggingface import HuggingFaceEmbeddings

from rag.config import cfg

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once and reused
_embeddings_instance: HuggingFaceEmbeddings | None = None


def get_embeddings(
    model_name: str | None = None,
    device: str | None = None,
) -> HuggingFaceEmbeddings:
    """
    Return a (cached) HuggingFaceEmbeddings instance.

    The first call downloads the model weights from HuggingFace Hub.
    Subsequent calls return the cached instance immediately.

    Args:
        model_name: Override the embedding model (default: cfg.EMBEDDING_MODEL).
        device:     Override the compute device, e.g. "cuda" (default: cfg.EMBEDDING_DEVICE).

    Returns:
        A LangChain-compatible HuggingFaceEmbeddings object.
    """
    global _embeddings_instance

    resolved_model = model_name or cfg.EMBEDDING_MODEL
    resolved_device = device or cfg.EMBEDDING_DEVICE

    # Return cached instance only if config matches
    if _embeddings_instance is not None:
        return _embeddings_instance

    logger.info(
        "Loading embedding model '%s' on device='%s' …",
        resolved_model,
        resolved_device,
    )

    _embeddings_instance = HuggingFaceEmbeddings(
        model_name=resolved_model,
        model_kwargs={"device": resolved_device},
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info("Embedding model loaded successfully.")
    return _embeddings_instance


def reset_embeddings() -> None:
    """Clear the cached embeddings instance (useful for testing)."""
    global _embeddings_instance
    _embeddings_instance = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings and return their vector representations.

    Args:
        texts: List of strings to embed.

    Returns:
        List of float vectors (one per input string).
    """
    embeddings = get_embeddings()
    return embeddings.embed_documents(texts)


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string (uses query-optimised encoding when available).

    Args:
        query: The search query to embed.

    Returns:
        Float vector.
    """
    embeddings = get_embeddings()
    return embeddings.embed_query(query)
