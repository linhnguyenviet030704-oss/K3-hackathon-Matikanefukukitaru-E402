import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search_skin import SearchDiagnostics, run_search


class FakeVoyage:
    def __init__(self):
        self.embed_calls = []
        self.rerank_calls = []

    def count_tokens(self, texts, model):
        return sum(len(t.split()) for t in texts)

    def embed(self, texts, model, input_type, truncation):
        self.embed_calls.append((texts, model, input_type, truncation))

        class Result:
            embeddings = [[1.0, 0.0] for _ in texts]

        return Result()

    def rerank(self, query, documents, model, top_k, truncation):
        self.rerank_calls.append((query, documents, model, top_k, truncation))

        class Item:
            def __init__(self, index):
                self.index = index
                self.relevance_score = 1.0 - index / 10

        class Result:
            results = [Item(i) for i in range(top_k)]

        return Result()


class FakeStores:
    def bm25(self, query, limit):
        return [
            {"id": "a", "document": "choc lo", "metadata": {}, "scores": {"bm25_raw": 3.0}, "source_ranks": {"bm25": 1}},
        ]

    def vector(self, query_embedding, limit):
        return [
            {
                "id": "b",
                "document": "nhiem khuan da",
                "metadata": {},
                "scores": {"cosine_distance": 0.2, "vector_similarity": 0.8},
                "source_ranks": {"vector": 1},
            }
        ]


def test_bm25_mode_does_not_call_api():
    voyage = FakeVoyage()
    diagnostics = SearchDiagnostics(mode="bm25", query="choc lo")

    out = run_search(FakeStores().bm25, FakeStores().vector, voyage, "choc lo", "bm25", 10, 10, "voyage-4", "rerank-2.5", diagnostics)

    assert [r["id"] for r in out] == ["a"]
    assert voyage.embed_calls == []
    assert voyage.rerank_calls == []


def test_vector_hybrid_and_rerank_call_expected_apis():
    for mode, expect_rerank in [("vector", 0), ("hybrid", 0), ("rerank", 1)]:
        voyage = FakeVoyage()
        diagnostics = SearchDiagnostics(mode=mode, query="nhiem khuan da")
        run_search(FakeStores().bm25, FakeStores().vector, voyage, "nhiem khuan da", mode, 10, 10, "voyage-4", "rerank-2.5", diagnostics)
        assert voyage.embed_calls[0][2] == "query"
        assert len(voyage.rerank_calls) == expect_rerank
