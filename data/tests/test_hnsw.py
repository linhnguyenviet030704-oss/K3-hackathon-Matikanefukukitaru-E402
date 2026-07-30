import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_index import get_chroma_collection


def test_hnsw_collection_uses_cosine_and_direct_query_embeddings(tmp_path):
    collection = get_chroma_collection(tmp_path / "chroma", "Skin")

    assert collection.configuration["hnsw"]["space"] == "cosine"
    assert collection.configuration["embedding_function"] is None

    collection.upsert(
        ids=["a", "b"],
        documents=["benh choc lo", "viem da co dia"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        metadatas=[{"_content_hash": "a"}, {"_content_hash": "b"}],
    )
    result = collection.query(query_embeddings=[[1.0, 0.0]], n_results=1, include=["distances"])

    assert result["ids"][0] == ["a"]
