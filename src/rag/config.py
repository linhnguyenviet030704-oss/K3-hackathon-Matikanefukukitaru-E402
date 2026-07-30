"""
rag/config.py — Centralised configuration loaded from environment variables.

All KB-related settings are read here so that individual modules
don't need to import dotenv directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (src/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class KBConfig:
    """Knowledge-base configuration with sensible defaults."""

    # ── Paths ──────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    RAW_DIR: Path = BASE_DIR / os.getenv("RAW_DIR", "data/raw")
    PROCESSED_DIR: Path = BASE_DIR / os.getenv("PROCESSED_DIR", "data/processed")
    CHUNKS_DIR: Path = PROCESSED_DIR / "chunks"
    METADATA_DIR: Path = PROCESSED_DIR / "metadata"
    VECTORSTORE_DIR: Path = BASE_DIR / os.getenv("VECTORSTORE_DIR", "data/vectorstore/chroma_db")

    # ── Collection ─────────────────────────────────────────────────────────
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "skin_disease_kb")

    # ── Embedding ──────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

    # ── Chunking ───────────────────────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    # ── Retrieval ──────────────────────────────────────────────────────────
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    RETRIEVAL_MODE: str = os.getenv("RETRIEVAL_MODE", "similarity")

    # ── Supported raw sub-folders and their source_type label ──────────────
    SOURCE_TYPE_MAP: dict[str, str] = {
        "textbooks": "textbook",
        "guidelines": "guideline",
        "articles": "article",
    }

    # ── Target skin diseases (ICD-10 mapping) ──────────────────────────────
    DISEASE_ICD_MAP: dict[str, str] = {
        "acne": "L70",
        "acne vulgaris": "L70",
        "atopic dermatitis": "L20",
        "eczema": "L20",
        "psoriasis": "L40",
        "rosacea": "L71",
        "tinea": "B35",
        "fungal": "B35",
        "urticaria": "L50",
        "hives": "L50",
        "melanoma": "C43",
        "basal cell carcinoma": "C44.9",
        "seborrheic dermatitis": "L21",
        "contact dermatitis": "L23",
    }


cfg = KBConfig()
