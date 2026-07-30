import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search_skin import combine_hybrid_results, min_max_normalize, rerank_candidates


def test_min_max_normalize_single_score_is_one():
    assert min_max_normalize(7, 7, 7) == 1.0


def test_hybrid_uses_normalized_scores_and_deterministic_tiebreak():
    bm25 = [
        {"id": "lex", "document": "lex", "metadata": {}, "scores": {"bm25_raw": 100.0}, "source_ranks": {"bm25": 1}},
        {"id": "both", "document": "both", "metadata": {}, "scores": {"bm25_raw": 90.0}, "source_ranks": {"bm25": 2}},
        {"id": "low1", "document": "low1", "metadata": {}, "scores": {"bm25_raw": 10.0}, "source_ranks": {"bm25": 3}},
    ]
    vector = [
        {"id": "vec", "document": "vec", "metadata": {}, "scores": {"cosine_distance": 0.0, "vector_similarity": 1.0}, "source_ranks": {"vector": 1}},
        {"id": "both", "document": "both", "metadata": {}, "scores": {"cosine_distance": 0.1, "vector_similarity": 0.9}, "source_ranks": {"vector": 2}},
        {"id": "low2", "document": "low2", "metadata": {}, "scores": {"cosine_distance": 0.9, "vector_similarity": 0.1}, "source_ranks": {"vector": 3}},
    ]

    out = combine_hybrid_results(bm25, vector, top_k=10)

    assert {r["id"] for r in out} == {"lex", "vec", "both", "low1", "low2"}
    assert out[0]["id"] == "both"
    assert out[0]["scores"]["hybrid"] > out[1]["scores"]["hybrid"]
    assert out[0]["source_ranks"] == {"bm25": 2, "vector": 2}
    assert out[1]["scores"]["bm25_normalized"] in (0.0, 1.0)
    assert out[1]["scores"]["vector_normalized"] in (0.0, 1.0)


class FakeReranker:
    def __init__(self):
        self.calls = []

    def rerank(self, query, documents, model, top_k, truncation):
        self.calls.append((query, documents, model, top_k, truncation))

        class Item:
            def __init__(self, index, relevance_score):
                self.index = index
                self.relevance_score = relevance_score

        class Result:
            results = [Item(1, 0.9), Item(0, 0.2)]

        return Result()


def test_reranker_maps_indexes_to_hybrid_candidates():
    client = FakeReranker()
    candidates = [
        {"rank": 1, "id": "a", "document": "A", "metadata": {}, "source_ranks": {"hybrid": 1}, "scores": {"hybrid": 2.0}},
        {"rank": 2, "id": "b", "document": "B", "metadata": {}, "source_ranks": {"hybrid": 2}, "scores": {"hybrid": 1.0}},
    ]

    out, calls = rerank_candidates(client, "q", candidates, top_k=2, model="rerank-2.5")

    assert client.calls[0] == ("q", ["A", "B"], "rerank-2.5", 2, False)
    assert calls == 1
    assert [r["id"] for r in out] == ["b", "a"]
    assert out[0]["scores"]["hybrid"] == 1.0
    assert out[0]["scores"]["reranker"] == 0.9
