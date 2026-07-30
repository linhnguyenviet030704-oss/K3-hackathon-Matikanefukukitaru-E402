from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from skin_index import MODEL, RollingRateLimiter, bm25_search, load_voyage_key, project_root, call_with_retry, get_chroma_collection, configure_stdio


@dataclass
class SearchDiagnostics:
    mode: str
    query: str
    bm25_candidates: int = 0
    vector_candidates: int = 0
    union_candidates: int = 0
    rerank_candidates: int = 0
    embedding_api_calls: int = 0
    reranker_api_calls: int = 0
    embedding_tokens: int = 0
    reranker_tokens: int = 0
    elapsed_seconds: float = 0.0


def min_max_normalize(score: float, min_score: float, max_score: float) -> float:
    if max_score == min_score:
        return 1.0
    return (score - min_score) / (max_score - min_score)


def normalize(items: list[dict], key: str, out_key: str) -> None:
    if not items:
        return
    vals = [float(i["scores"][key]) for i in items]
    lo, hi = min(vals), max(vals)
    for item in items:
        item["scores"][out_key] = min_max_normalize(float(item["scores"][key]), lo, hi)


def combine_hybrid_results(bm25: list[dict], vector: list[dict], top_k: int) -> list[dict]:
    bm25 = [dict(r, scores=dict(r["scores"]), source_ranks=dict(r.get("source_ranks", {}))) for r in bm25]
    vector = [dict(r, scores=dict(r["scores"]), source_ranks=dict(r.get("source_ranks", {}))) for r in vector]
    normalize(bm25, "bm25_raw", "bm25_normalized")
    normalize(vector, "vector_similarity", "vector_normalized")

    merged: dict[str, dict] = {}
    for item in bm25:
        merged[item["id"]] = item
        merged[item["id"]]["source_ranks"] = {"bm25": item["source_ranks"].get("bm25"), "vector": None}
    for item in vector:
        current = merged.setdefault(item["id"], item)
        current.setdefault("scores", {}).update({k: v for k, v in item["scores"].items() if v is not None})
        current["source_ranks"] = {
            "bm25": current.get("source_ranks", {}).get("bm25"),
            "vector": item["source_ranks"].get("vector"),
        }

    for item in merged.values():
        scores = item["scores"]
        scores.setdefault("bm25_raw", None)
        scores.setdefault("bm25_normalized", 0.0)
        scores.setdefault("cosine_distance", None)
        scores.setdefault("vector_similarity", None)
        scores.setdefault("vector_normalized", 0.0)
        scores.setdefault("reranker", None)
        if scores["bm25_normalized"] is None:
            scores["bm25_normalized"] = 0.0
        if scores["vector_normalized"] is None:
            scores["vector_normalized"] = 0.0
        scores["hybrid"] = scores["bm25_normalized"] + scores["vector_normalized"]

    def rank_sum(item: dict) -> int:
        ranks = item["source_ranks"]
        return (ranks.get("bm25") or 10**9) + (ranks.get("vector") or 10**9)

    ranked = sorted(
        merged.values(),
        key=lambda i: (-i["scores"]["hybrid"], -max(i["scores"]["bm25_normalized"], i["scores"]["vector_normalized"]), rank_sum(i), i["id"]),
    )
    for rank, item in enumerate(ranked[:top_k], start=1):
        item["rank"] = rank
    return ranked[:top_k]


def embed_query(voyage_client, query: str, model: str, diagnostics: SearchDiagnostics) -> list[float]:
    tokens = voyage_client.count_tokens([query], model=model)
    diagnostics.embedding_tokens += int(tokens)
    limiter = RollingRateLimiter()

    def request():
        limiter.wait(int(tokens))
        return voyage_client.embed(texts=[query], model=model, input_type="query", truncation=False)

    result = call_with_retry(request)
    diagnostics.embedding_api_calls += 1
    return result.embeddings[0]


def rerank_candidates(voyage_client, query: str, candidates: list[dict], top_k: int, model: str) -> tuple[list[dict], int]:
    if not candidates:
        return [], 0
    docs = [r["document"] for r in candidates]
    result = call_with_retry(lambda: voyage_client.rerank(query=query, documents=docs, model=model, top_k=min(top_k, len(docs)), truncation=False))
    items = getattr(result, "results", result)
    out = []
    for item in items:
        idx = getattr(item, "index", None)
        score = getattr(item, "relevance_score", None)
        if idx is None or idx < 0 or idx >= len(candidates) or score is None:
            raise SystemExit("Reranker trả về index hoặc score không hợp lệ.")
        row = dict(candidates[idx], scores=dict(candidates[idx]["scores"]), source_ranks=dict(candidates[idx].get("source_ranks", {})))
        row["source_ranks"]["hybrid"] = candidates[idx]["rank"]
        row["scores"]["reranker"] = float(score)
        out.append(row)
    out.sort(key=lambda r: -r["scores"]["reranker"])
    for rank, row in enumerate(out, start=1):
        row["rank"] = rank
    return out, 1


def run_search(bm25_fn, vector_fn, voyage_client, query: str, mode: str, top_k: int, candidate_k: int, embedding_model: str, reranker_model: str, diagnostics: SearchDiagnostics) -> list[dict]:
    if mode == "bm25":
        rows = bm25_fn(query, candidate_k)
        diagnostics.bm25_candidates = len(rows)
        return rows[:top_k]

    query_embedding = embed_query(voyage_client, query, embedding_model, diagnostics)
    vector = vector_fn(query_embedding, candidate_k)
    diagnostics.vector_candidates = len(vector)
    if mode == "vector":
        return vector[:top_k]

    bm25 = bm25_fn(query, candidate_k)
    diagnostics.bm25_candidates = len(bm25)
    hybrid = combine_hybrid_results(bm25, vector, candidate_k)
    diagnostics.union_candidates = len({r["id"] for r in bm25 + vector})
    if mode == "hybrid":
        return hybrid[:top_k]

    if mode == "rerank":
        diagnostics.rerank_candidates = len(hybrid[:candidate_k])
        out, calls = rerank_candidates(voyage_client, query, hybrid[:candidate_k], top_k, reranker_model)
        diagnostics.reranker_api_calls += calls
        return out
    raise SystemExit(f"Mode không hợp lệ: {mode}")


def chroma_vector_search(collection, query_embedding: list[float], limit: int) -> list[dict]:
    result = collection.query(query_embeddings=[query_embedding], n_results=limit, include=["documents", "metadatas", "distances"])
    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    rows = []
    for rank, (row_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances), start=1):
        sim = 1.0 - float(dist)
        rows.append(
            {
                "rank": rank,
                "id": row_id,
                "document": doc,
                "metadata": meta or {},
                "source_ranks": {"bm25": None, "vector": rank},
                "scores": {
                    "bm25_raw": None,
                    "bm25_normalized": None,
                    "cosine_distance": float(dist),
                    "vector_similarity": sim,
                    "vector_normalized": None,
                    "hybrid": None,
                    "reranker": None,
                },
            }
        )
    rows.sort(key=lambda r: -r["scores"]["vector_similarity"])
    return rows


def print_diagnostics(d: SearchDiagnostics) -> None:
    print(f"Mode: {d.mode}", file=sys.stderr)
    print(f"Query: {d.query}", file=sys.stderr)
    print(f"BM25 candidate count: {d.bm25_candidates}", file=sys.stderr)
    print(f"Vector candidate count: {d.vector_candidates}", file=sys.stderr)
    print(f"Union candidate count: {d.union_candidates}", file=sys.stderr)
    print(f"Rerank candidate count: {d.rerank_candidates}", file=sys.stderr)
    print(f"Embedding API calls: {d.embedding_api_calls}", file=sys.stderr)
    print(f"Reranker API calls: {d.reranker_api_calls}", file=sys.stderr)
    print(f"Embedding tokens: {d.embedding_tokens}", file=sys.stderr)
    print(f"Reranker tokens: {d.reranker_tokens}", file=sys.stderr)
    print(f"Elapsed time: {d.elapsed_seconds:.2f}s", file=sys.stderr)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", choices=["bm25", "vector", "hybrid", "rerank"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=10)
    parser.add_argument("--collection", default="Skin")
    parser.add_argument("--persist-dir", type=Path, default=project_root() / "data" / "chroma_db")
    parser.add_argument("--bm25-db", type=Path, default=project_root() / "data" / "search_index.sqlite3")
    parser.add_argument("--embedding-model", default=MODEL)
    parser.add_argument("--reranker-model", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-metadata", action="store_true")
    args = parser.parse_args()

    query = args.query.strip()
    if not query:
        raise SystemExit("--query không được rỗng.")
    reranker_model = args.reranker_model or os.getenv("VOYAGE_RERANK_MODEL") or "rerank-2.5"
    diagnostics = SearchDiagnostics(mode=args.mode, query=query)
    start = time.time()

    voyage_client = None
    if args.mode != "bm25":
        load_voyage_key()
        import voyageai

        voyage_client = voyageai.Client()
    collection = None
    if args.mode != "bm25":
        collection = get_chroma_collection(args.persist_dir, args.collection, model=args.embedding_model)
        meta = collection.metadata or {}
        if meta.get("embedding_model") and meta["embedding_model"] != args.embedding_model:
            raise SystemExit("Embedding model của collection không khớp --embedding-model.")

    bm25_fn = lambda q, k: bm25_search(args.bm25_db, q, k)
    vector_fn = lambda emb, k: chroma_vector_search(collection, emb, k)
    results = run_search(bm25_fn, vector_fn, voyage_client, query, args.mode, args.top_k, args.candidate_k, args.embedding_model, reranker_model, diagnostics)
    diagnostics.elapsed_seconds = time.time() - start
    print_diagnostics(diagnostics)

    payload = {
        "query": query,
        "mode": args.mode,
        "top_k": args.top_k,
        "candidate_k": args.candidate_k,
        "collection": args.collection,
        "embedding_model": args.embedding_model,
        "reranker_model": reranker_model if args.mode == "rerank" else None,
        "results": results,
        "diagnostics": diagnostics.__dict__,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print(f"{row['rank']}. {row['id']} score={row['scores']}")
            print(row["document"][:800].replace("\n", " "))
            if args.show_metadata:
                print(json.dumps(row["metadata"], ensure_ascii=False))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
