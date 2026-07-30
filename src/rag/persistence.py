"""
rag/persistence.py — Save/load processed chunks to/from data/processed/.

After chunking, chunks are saved as JSON for inspection and reproducibility.
The build pipeline can skip re-loading raw files if processed chunks already exist.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.documents import Document

from rag.config import cfg

logger = logging.getLogger(__name__)


def save_chunks(
    documents: list[Document],
    chunks_dir: Path | None = None,
) -> Path:
    """
    Serialize LangChain Documents to a JSON file in *chunks_dir*.

    File name: ``chunks_<count>.json``

    Args:
        documents:  List of LangChain Document objects to persist.
        chunks_dir: Directory to write into (default: cfg.CHUNKS_DIR).

    Returns:
        Path to the saved JSON file.
    """
    out_dir = Path(chunks_dir or cfg.CHUNKS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in documents
    ]

    out_file = out_dir / f"chunks_{len(documents)}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d chunks to %s", len(documents), out_file)
    return out_file


def load_chunks(chunks_dir: Path | None = None) -> list[Document]:
    """
    Load all chunk JSON files from *chunks_dir* and reconstruct Documents.

    Args:
        chunks_dir: Directory containing chunk JSON files.

    Returns:
        List of LangChain Document objects.
    """
    in_dir = Path(chunks_dir or cfg.CHUNKS_DIR)
    if not in_dir.exists():
        logger.warning("Chunks directory not found: %s", in_dir)
        return []

    documents: list[Document] = []
    json_files = sorted(in_dir.glob("*.json"))

    if not json_files:
        logger.warning("No chunk JSON files found in: %s", in_dir)
        return []

    for json_file in json_files:
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
            for item in payload:
                documents.append(
                    Document(
                        page_content=item["page_content"],
                        metadata=item.get("metadata", {}),
                    )
                )
        except Exception as exc:
            logger.error("Failed to load chunks from %s: %s", json_file, exc)

    logger.info("Loaded %d chunks from %s", len(documents), in_dir)
    return documents


def chunks_exist(chunks_dir: Path | None = None) -> bool:
    """Return True if at least one chunk JSON file exists."""
    in_dir = Path(chunks_dir or cfg.CHUNKS_DIR)
    return in_dir.exists() and any(in_dir.glob("*.json"))
