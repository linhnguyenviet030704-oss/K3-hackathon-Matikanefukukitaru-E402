"""
tests/unit/test_knowledge_base.py — Unit tests for Task 01: Knowledge Base.

Covers:
  - rag.loaders     : load_documents, individual loaders
  - rag.cleaner     : full_clean, remove_repeated_header_footer
  - rag.chunker     : DocumentChunker, _detect_disease_and_icd, _detect_language
  - rag.persistence : save_chunks, load_chunks, chunks_exist
  - rag.vectorstore : build_vectorstore, load_vectorstore, similarity_search
  - rag.embedder    : get_embeddings (mocked)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the src/ directory is on the path when running pytest from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_text() -> str:
    return (
        "Psoriasis is a chronic autoimmune skin condition that causes rapid buildup "
        "of skin cells. This buildup of cells causes scaling on the skin's surface. "
        "Inflammation and redness around the scales is fairly common. "
        "Typical psoriatic scales are whitish-silver and develop in thick, red patches. "
        "Sometimes, these patches will crack and bleed.\n\n"
        "Acne vulgaris is the most common skin disease affecting adolescents and young adults. "
        "It is characterized by comedones, papules, pustules, and nodules. "
        "Treatment options include topical retinoids and benzoyl peroxide.\n\n"
        "Atopic dermatitis (eczema) is a condition that makes your skin red and itchy. "
        "It is common in children but can occur at any age."
    )


@pytest.fixture
def sample_raw_doc(sample_text):
    from rag.loaders import RawDocument
    return RawDocument(
        text=sample_text,
        source_file="test_document.txt",
        source_type="article",
        file_format="txt",
    )


# ─────────────────────────────────────────────────────────────────────────────
# rag.cleaner
# ─────────────────────────────────────────────────────────────────────────────

class TestCleaner:

    def test_clean_text_removes_control_chars(self):
        from rag.cleaner import clean_text
        dirty = "Hello\x00World\x01test"
        result = clean_text(dirty)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "Hello" in result
        assert "World" in result

    def test_clean_text_collapses_blank_lines(self):
        from rag.cleaner import clean_text
        text = "Line 1\n\n\n\n\nLine 2"
        result = clean_text(text)
        # Cleaner collapses to at most 1 consecutive blank line
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_clean_text_normalises_whitespace(self):
        from rag.cleaner import clean_text
        text = "  Too   many    spaces  "
        result = clean_text(text)
        assert "  " not in result  # No double spaces after strip

    def test_clean_text_empty_string(self):
        from rag.cleaner import clean_text
        assert clean_text("") == ""

    def test_remove_repeated_header_footer(self):
        from rag.cleaner import remove_repeated_header_footer
        repeated_line = "Page Header"
        text = f"{repeated_line}\nContent 1\n{repeated_line}\nContent 2\n{repeated_line}\nContent 3"
        result = remove_repeated_header_footer(text, min_occurrences=3)
        assert repeated_line not in result
        assert "Content 1" in result
        assert "Content 2" in result

    def test_full_clean_returns_non_empty(self, sample_text):
        from rag.cleaner import full_clean
        result = full_clean(sample_text)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_full_clean_preserves_medical_terms(self, sample_text):
        from rag.cleaner import full_clean
        result = full_clean(sample_text)
        assert "psoriasis" in result.lower()
        assert "acne" in result.lower()
        assert "eczema" in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# rag.loaders
# ─────────────────────────────────────────────────────────────────────────────

class TestLoaders:

    def test_load_txt(self, tmp_path):
        from rag.loaders import load_txt
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, this is a test skin disease article.", encoding="utf-8")
        doc = load_txt(txt_file, source_type="article")
        assert "Hello" in doc.text
        assert doc.source_type == "article"
        assert doc.file_format == "txt"

    def test_load_documents_empty_dir(self, tmp_path):
        from rag.loaders import load_documents
        docs = load_documents(tmp_path)
        assert docs == []

    def test_load_documents_nonexistent_dir(self, tmp_path):
        from rag.loaders import load_documents
        docs = load_documents(tmp_path / "nonexistent")
        assert docs == []

    def test_load_documents_skips_unsupported(self, tmp_path):
        from rag.loaders import load_documents
        (tmp_path / "image.png").write_bytes(b"fake image")
        (tmp_path / "data.csv").write_text("col1,col2\n1,2")
        docs = load_documents(tmp_path)
        assert docs == []

    def test_load_documents_with_txt_files(self, tmp_path):
        from rag.loaders import load_documents
        articles = tmp_path / "articles"
        articles.mkdir()
        (articles / "doc1.txt").write_text("Psoriasis is a skin disease.", encoding="utf-8")
        (articles / "doc2.txt").write_text("Acne affects many teenagers.", encoding="utf-8")
        docs = load_documents(tmp_path)
        assert len(docs) == 2
        source_types = {d.source_type for d in docs}
        assert "article" in source_types

    def test_source_type_inferred_from_folder(self, tmp_path):
        from rag.loaders import load_documents
        for folder in ("textbooks", "guidelines", "articles"):
            sub = tmp_path / folder
            sub.mkdir()
            (sub / "doc.txt").write_text(f"Content in {folder}.", encoding="utf-8")
        docs = load_documents(tmp_path)
        source_types = {d.source_type for d in docs}
        assert "textbook" in source_types
        assert "guideline" in source_types
        assert "article" in source_types


# ─────────────────────────────────────────────────────────────────────────────
# rag.chunker
# ─────────────────────────────────────────────────────────────────────────────

class TestChunker:

    def test_chunk_produces_multiple_chunks(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        docs = chunker.chunk(sample_raw_doc)
        assert len(docs) > 1, "Long text should produce multiple chunks"

    def test_chunk_size_respected(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunk_size = 200
        chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=20)
        docs = chunker.chunk(sample_raw_doc)
        for doc in docs:
            # LangChain splitter may exceed by a small margin on last chunk
            assert len(doc.page_content) <= chunk_size + 50

    def test_chunk_metadata_schema(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunker = DocumentChunker(chunk_size=300, chunk_overlap=30)
        docs = chunker.chunk(sample_raw_doc)
        assert len(docs) > 0
        for doc in docs:
            meta = doc.metadata
            assert "chunk_id" in meta
            assert "source_file" in meta
            assert "source_type" in meta
            assert "chunk_index" in meta
            assert "created_at" in meta
            assert "language" in meta
            assert meta["source_file"] == "test_document.txt"

    def test_chunk_detects_disease_psoriasis(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunker = DocumentChunker(chunk_size=300, chunk_overlap=30)
        docs = chunker.chunk(sample_raw_doc)
        diseases = [d.metadata.get("disease_category", "") for d in docs]
        assert any("Psoriasis" in d for d in diseases)

    def test_chunk_detects_icd_code(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunker = DocumentChunker(chunk_size=300, chunk_overlap=30)
        docs = chunker.chunk(sample_raw_doc)
        icds = [d.metadata.get("icd_code", "") for d in docs]
        # Psoriasis = L40, Acne = L70, Eczema = L20
        assert any(icd in ("L40", "L70", "L20") for icd in icds)

    def test_chunk_empty_text_returns_empty(self):
        from rag.chunker import DocumentChunker
        from rag.loaders import RawDocument
        chunker = DocumentChunker()
        empty_doc = RawDocument(text="", source_file="empty.txt", source_type="article", file_format="txt")
        docs = chunker.chunk(empty_doc)
        assert docs == []

    def test_chunk_all_combines_multiple_docs(self, sample_raw_doc):
        from rag.chunker import DocumentChunker
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        docs = chunker.chunk_all([sample_raw_doc, sample_raw_doc])
        # Should produce at least 2× as many chunks as a single doc
        single = chunker.chunk(sample_raw_doc)
        assert len(docs) >= len(single) * 2

    def test_detect_language_english(self):
        from rag.chunker import _detect_language
        assert _detect_language("This is a plain English text about psoriasis.") == "en"

    def test_detect_language_vietnamese(self):
        from rag.chunker import _detect_language
        vi_text = "Vảy nến là bệnh da liễu mãn tính ảnh hưởng đến nhiều người."
        assert _detect_language(vi_text) == "vi"


# ─────────────────────────────────────────────────────────────────────────────
# rag.persistence
# ─────────────────────────────────────────────────────────────────────────────

class TestPersistence:

    def test_save_and_load_chunks(self, tmp_path, sample_raw_doc):
        from rag.chunker import DocumentChunker
        from rag.persistence import save_chunks, load_chunks

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        docs = chunker.chunk(sample_raw_doc)

        saved_path = save_chunks(docs, chunks_dir=tmp_path)
        assert saved_path.exists()

        loaded = load_chunks(chunks_dir=tmp_path)
        assert len(loaded) == len(docs)
        assert loaded[0].page_content == docs[0].page_content
        assert loaded[0].metadata["chunk_id"] == docs[0].metadata["chunk_id"]

    def test_chunks_exist_false_when_empty(self, tmp_path):
        from rag.persistence import chunks_exist
        assert chunks_exist(tmp_path) is False

    def test_chunks_exist_true_after_save(self, tmp_path, sample_raw_doc):
        from rag.chunker import DocumentChunker
        from rag.persistence import save_chunks, chunks_exist

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        docs = chunker.chunk(sample_raw_doc)
        save_chunks(docs, chunks_dir=tmp_path)
        assert chunks_exist(tmp_path) is True

    def test_load_chunks_empty_dir(self, tmp_path):
        from rag.persistence import load_chunks
        docs = load_chunks(chunks_dir=tmp_path)
        assert docs == []

    def test_saved_json_is_valid(self, tmp_path, sample_raw_doc):
        from rag.chunker import DocumentChunker
        from rag.persistence import save_chunks

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        docs = chunker.chunk(sample_raw_doc)
        saved_path = save_chunks(docs, chunks_dir=tmp_path)

        payload = json.loads(saved_path.read_text(encoding="utf-8"))
        assert isinstance(payload, list)
        assert len(payload) == len(docs)
        for item in payload:
            assert "page_content" in item
            assert "metadata" in item


# ─────────────────────────────────────────────────────────────────────────────
# rag.embedder (mocked — no model download in tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestEmbedder:

    def setup_method(self):
        from rag import embedder
        embedder.reset_embeddings()

    def test_get_embeddings_returns_instance(self):
        from rag.embedder import get_embeddings
        from langchain_huggingface import HuggingFaceEmbeddings

        mock_emb = MagicMock(spec=HuggingFaceEmbeddings)
        with patch("rag.embedder.HuggingFaceEmbeddings", return_value=mock_emb):
            emb = get_embeddings()
        assert emb is mock_emb

    def test_get_embeddings_cached(self):
        from rag.embedder import get_embeddings
        from langchain_huggingface import HuggingFaceEmbeddings

        mock_emb = MagicMock(spec=HuggingFaceEmbeddings)
        with patch("rag.embedder.HuggingFaceEmbeddings", return_value=mock_emb) as MockCls:
            get_embeddings()
            get_embeddings()
        # Constructor called only once despite two calls
        MockCls.assert_called_once()

    def test_embed_texts_calls_embed_documents(self):
        from rag import embedder

        mock_emb = MagicMock()
        mock_emb.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
        embedder._embeddings_instance = mock_emb

        result = embedder.embed_texts(["hello", "world"])
        mock_emb.embed_documents.assert_called_once_with(["hello", "world"])
        assert len(result) == 2

    def test_embed_query_calls_embed_query(self):
        from rag import embedder

        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.5, 0.6, 0.7]
        embedder._embeddings_instance = mock_emb

        result = embedder.embed_query("psoriasis symptoms")
        mock_emb.embed_query.assert_called_once_with("psoriasis symptoms")
        assert result == [0.5, 0.6, 0.7]


# ─────────────────────────────────────────────────────────────────────────────
# rag.vectorstore (mocked — no real ChromaDB in unit tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestVectorstore:

    def test_build_vectorstore_raises_on_empty_docs(self):
        from rag.vectorstore import build_vectorstore
        with pytest.raises(ValueError, match="No documents"):
            build_vectorstore([])

    def test_load_vectorstore_raises_on_missing_dir(self, tmp_path):
        from rag.vectorstore import load_vectorstore
        missing = tmp_path / "nonexistent_chroma"
        with pytest.raises(FileNotFoundError):
            load_vectorstore(persist_directory=str(missing))
