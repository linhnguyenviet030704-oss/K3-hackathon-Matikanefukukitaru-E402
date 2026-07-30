"""
rag/ — Retrieval-Augmented Generation package for AI Dermatology Assistant.

Modules:
    loaders     — Load raw documents (PDF, DOCX, TXT) from data/raw/
    cleaner     — Text cleaning and normalization
    chunker     — Split documents into overlapping chunks with metadata
    embedder    — Embedding model wrapper (BAAI/bge-m3)
    vectorstore — ChromaDB CRUD operations
    build_kb    — End-to-end pipeline: raw → processed → vectorstore
"""
