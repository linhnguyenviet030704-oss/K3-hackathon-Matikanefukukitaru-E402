"""
rag/vectorstore.py — ChromaDB CRUD operations.

Provides:
  - build_vectorstore()  : Create a new collection from LangChain Documents.
  - load_vectorstore()   : Load an existing persisted collection.
  - get_retriever()      : Return a LangChain retriever ready for RAG.
  - collection_info()    : Print statistics about the stored collection.
  - delete_collection()  : Drop the collection (useful for full rebuild).
"""

from __future__ import annotations

import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from rag.config import cfg
from rag.embedder import get_embeddings

logger = logging.getLogger(__name__)


def build_vectorstore(
    documents: list[Document],
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> Chroma:
    """
    Embed *documents* and persist them to ChromaDB.

    If the collection already exists at *persist_directory*, the existing
    data is REPLACED (full rebuild). Use load_vectorstore() to add to an
    existing collection.

    Args:
        documents:         LangChain Documents to index.
        persist_directory: Override the default storage path.
        collection_name:   Override the default collection name.

    Returns:
        A Chroma vectorstore instance.
    """
    persist_dir = str(persist_directory or cfg.VECTORSTORE_DIR)
    coll_name = collection_name or cfg.COLLECTION_NAME
    embeddings = get_embeddings()

    if not documents:
        raise ValueError("No documents provided to build_vectorstore().")

    logger.info(
        "Building ChromaDB collection '%s' with %d documents at '%s' …",
        coll_name,
        len(documents),
        persist_dir,
    )

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=coll_name,
    )

    count = vectorstore._collection.count()
    logger.info("ChromaDB collection built — %d vectors stored.", count)
    return vectorstore


def load_vectorstore(
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> Chroma:
    """
    Load an existing persisted ChromaDB collection.

    Args:
        persist_directory: Path to the ChromaDB storage directory.
        collection_name:   Name of the collection to load.

    Returns:
        A Chroma vectorstore instance.

    Raises:
        FileNotFoundError: If the persist_directory does not exist.
    """
    import os

    persist_dir = str(persist_directory or cfg.VECTORSTORE_DIR)
    coll_name = collection_name or cfg.COLLECTION_NAME

    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"ChromaDB directory not found: '{persist_dir}'. "
            "Run build_kb.py first to create the knowledge base."
        )

    embeddings = get_embeddings()

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name=coll_name,
    )

    count = vectorstore._collection.count()
    logger.info(
        "Loaded ChromaDB collection '%s' — %d vectors.", coll_name, count
    )
    return vectorstore


def get_retriever(
    vectorstore: Chroma | None = None,
    top_k: int | None = None,
    mode: str | None = None,
) -> VectorStoreRetriever:
    """
    Return a LangChain retriever from a (loaded or new) Chroma vectorstore.

    Args:
        vectorstore: An existing Chroma instance. If None, loads from disk.
        top_k:       Number of results to return (default: cfg.TOP_K).
        mode:        "similarity" | "mmr" | "similarity_score_threshold"
                     (default: cfg.RETRIEVAL_MODE).

    Returns:
        A LangChain VectorStoreRetriever.
    """
    vs = vectorstore or load_vectorstore()
    k = top_k or cfg.TOP_K
    search_type = mode or cfg.RETRIEVAL_MODE

    search_kwargs: dict = {"k": k}

    # MMR adds diversity by penalising redundant results
    if search_type == "mmr":
        search_kwargs["fetch_k"] = k * 3
        search_kwargs["lambda_mult"] = 0.7

    return vs.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )


def collection_info(
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> dict:
    """
    Return statistics about the stored ChromaDB collection.

    Returns:
        dict with keys: collection_name, total_vectors, persist_directory.
    """
    vs = load_vectorstore(persist_directory, collection_name)
    count = vs._collection.count()
    info = {
        "collection_name": collection_name or cfg.COLLECTION_NAME,
        "total_vectors": count,
        "persist_directory": str(persist_directory or cfg.VECTORSTORE_DIR),
    }
    logger.info("Collection info: %s", info)
    return info


def delete_collection(
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> None:
    """
    Drop the ChromaDB collection (irreversible).

    Useful before a full knowledge-base rebuild.
    """
    vs = load_vectorstore(persist_directory, collection_name)
    coll_name = collection_name or cfg.COLLECTION_NAME
    vs._client.delete_collection(coll_name)
    logger.warning("Deleted ChromaDB collection: '%s'", coll_name)


def similarity_search(
    query: str,
    k: int | None = None,
    vectorstore: Chroma | None = None,
) -> list[Document]:
    """
    Run a similarity search and return the top-k matching Documents.

    Convenience wrapper around Chroma.similarity_search().

    Args:
        query:       The search string.
        k:           Number of results (default: cfg.TOP_K).
        vectorstore: Optional pre-loaded Chroma instance.

    Returns:
        List of LangChain Document objects.
    """
    vs = vectorstore or load_vectorstore()
    return vs.similarity_search(query, k=k or cfg.TOP_K)
