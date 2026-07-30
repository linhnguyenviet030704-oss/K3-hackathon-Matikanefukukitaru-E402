from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from tqdm import tqdm

from skin_index import (
    INPUT_TYPE_DOCUMENT,
    MAX_BATCH_ITEMS,
    MODEL,
    TOKEN_BUDGET,
    RollingRateLimiter,
    bm25_count,
    bm25_exists,
    call_with_retry,
    collection_get_existing,
    find_jsonl_input,
    flatten_metadata,
    get_chroma_collection,
    get_text,
    load_voyage_key,
    project_root,
    sha256_text,
    stable_id,
    upsert_bm25,
    utc_now,
    configure_stdio,
)


@dataclass
class Report:
    input_file: str = ""
    collection: str = "Skin"
    model: str = MODEL
    chroma_path: str = "data/chroma_db"
    total_lines: int = 0
    valid_rows: int = 0
    inserted: int = 0
    updated: int = 0
    skipped_unchanged: int = 0
    failed: int = 0
    api_requests: int = 0
    total_tokens: int = 0
    rate_limit_wait_seconds: float = 0.0
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    bm25_inserted: int = 0
    bm25_updated: int = 0
    bm25_repaired: int = 0
    bm25_failed: int = 0
    text_field: str = ""


def write_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()


def write_report(path: Path, report: Report, collection_count: int, bm25_docs: int, hnsw: dict) -> None:
    data = asdict(report)
    data["vector_index"] = hnsw
    data["bm25_index"] = {"type": "SQLite FTS5 BM25", "path": "data/search_index.sqlite3", "indexed_documents": bm25_docs}
    data["collection_count"] = collection_count
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def count_tokens(client, texts: list[str], model: str) -> int:
    value = client.count_tokens(texts, model=model)
    return int(getattr(value, "total_tokens", value))


def embed_batch(client, limiter: RollingRateLimiter, texts: list[str], tokens: int, model: str):
    def request():
        limiter.wait(tokens)
        return client.embed(texts=texts, model=model, input_type=INPUT_TYPE_DOCUMENT, truncation=False)

    return call_with_retry(request)


def split_bad_batch(process_one, batch: list[dict]) -> None:
    if len(batch) == 1:
        process_one(batch[0])
        return
    mid = len(batch) // 2
    split_bad_batch(process_one, batch[:mid])
    split_bad_batch(process_one, batch[mid:])


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--text-field")
    parser.add_argument("--collection", default="Skin")
    parser.add_argument("--persist-dir", type=Path, default=project_root() / "data" / "chroma_db")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--hnsw-ef-construction", type=int, default=200)
    parser.add_argument("--hnsw-ef-search", type=int, default=100)
    parser.add_argument("--hnsw-max-neighbors", type=int, default=32)
    parser.add_argument("--rebuild-hnsw", action="store_true")
    args = parser.parse_args()

    root = project_root()
    data_dir = root / "data"
    input_file = (args.input or find_jsonl_input(data_dir)).resolve()
    failed_path = data_dir / "failed_rows.jsonl"
    report_path = data_dir / "ingestion_report.json"
    bm25_db = data_dir / "search_index.sqlite3"
    if failed_path.exists():
        failed_path.unlink()

    load_voyage_key()
    import voyageai

    client = voyageai.Client()
    limiter = RollingRateLimiter()
    collection = None if args.dry_run else get_chroma_collection(
        args.persist_dir,
        args.collection,
        args.hnsw_ef_construction,
        args.hnsw_ef_search,
        args.hnsw_max_neighbors,
        args.model,
        args.rebuild_hnsw,
    )
    hnsw = {
        "type": "HNSW",
        "space": "cosine",
        "ef_construction": args.hnsw_ef_construction,
        "ef_search": args.hnsw_ef_search,
        "max_neighbors": args.hnsw_max_neighbors,
    }
    start_monotonic = time.monotonic()
    report = Report(input_file=str(input_file), collection=args.collection, model=args.model, chroma_path=str(args.persist_dir), started_at=utc_now())
    batch: list[dict] = []
    predicted_batches = 0

    def flush_batch(items: list[dict]) -> None:
        nonlocal predicted_batches
        if not items:
            return
        predicted_batches += 1
        if args.dry_run:
            return
        texts = [i["text"] for i in items]
        tokens = sum(i["tokens"] for i in items)
        result = embed_batch(client, limiter, texts, tokens, args.model)
        embeddings = result.embeddings
        if len(embeddings) != len(texts):
            raise SystemExit("Voyage trả về số embedding không khớp batch.")
        collection.upsert(
            ids=[i["id"] for i in items],
            documents=texts,
            embeddings=embeddings,
            metadatas=[i["metadata"] for i in items],
        )
        try:
            upsert_bm25(bm25_db, [(i["id"], i["text"], i["metadata"], i["content_hash"]) for i in items])
            report.bm25_inserted += sum(1 for i in items if i["state"] == "inserted")
            report.bm25_updated += sum(1 for i in items if i["state"] == "updated")
        except Exception as exc:
            report.bm25_failed += len(items)
            for i in items:
                write_jsonl(failed_path, {"line": i["line"], "id": i["id"], "error": "bm25_sync_pending", "detail": str(exc)})
        report.api_requests += 1
        report.total_tokens += tokens
        report.inserted += sum(1 for i in items if i["state"] == "inserted")
        report.updated += sum(1 for i in items if i["state"] == "updated")
        write_report(report_path, report, collection.count(), bm25_count(bm25_db), hnsw)

    try:
        with input_file.open("r", encoding="utf-8-sig") as f:
            for line_no, line in enumerate(tqdm(f, desc="ingest"), start=1):
                report.total_lines = line_no
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                    if not isinstance(row, dict):
                        raise ValueError("row is not a JSON object")
                except Exception as exc:
                    report.failed += 1
                    write_jsonl(failed_path, {"line": line_no, "raw": raw, "error": "invalid_json", "detail": str(exc)})
                    continue
                text, used_field = get_text(row, args.text_field)
                if not text:
                    report.failed += 1
                    write_jsonl(failed_path, {"line": line_no, "keys": list(row.keys()), "error": "missing_text_field"})
                    continue
                report.text_field = report.text_field or used_field or ""
                content_hash = sha256_text(text)
                row_id = stable_id(row, input_file, line_no, text)
                metadata = flatten_metadata(row, used_field or "text", input_file, line_no, content_hash, args.model)
                report.valid_rows += 1

                existing_meta, existing_doc = (None, None) if args.dry_run else collection_get_existing(collection, row_id)
                if existing_meta and existing_meta.get("_content_hash") == content_hash:
                    if not bm25_exists(bm25_db, row_id):
                        upsert_bm25(bm25_db, [(row_id, existing_doc or text, existing_meta, content_hash)])
                        report.bm25_repaired += 1
                    report.skipped_unchanged += 1
                    continue

                tokens = count_tokens(client, [text], args.model)
                if tokens > TOKEN_BUDGET:
                    report.failed += 1
                    write_jsonl(failed_path, {"line": line_no, "id": row_id, "error": "single_chunk_exceeds_tpm_limit", "tokens": tokens})
                    continue
                state = "updated" if existing_meta else "inserted"
                item = {"id": row_id, "line": line_no, "text": text, "metadata": metadata, "content_hash": content_hash, "tokens": tokens, "state": state}
                if sum(i["tokens"] for i in batch) + tokens > TOKEN_BUDGET or len(batch) >= MAX_BATCH_ITEMS:
                    flush_batch(batch)
                    batch = []
                batch.append(item)
        flush_batch(batch)
    except KeyboardInterrupt:
        print("Đã nhận Ctrl+C, ghi report tạm thời.", file=sys.stderr)
        return 130
    finally:
        report.finished_at = utc_now()
        report.duration_seconds = time.monotonic() - start_monotonic
        report.rate_limit_wait_seconds = limiter.wait_seconds
        if args.dry_run:
            print(f"Dry-run predicted batches: {predicted_batches}")
            write_report(report_path, report, 0, bm25_count(bm25_db), hnsw)
        elif collection is not None:
            write_report(report_path, report, collection.count(), bm25_count(bm25_db), hnsw)

    if not args.dry_run:
        print(f"Collection {args.collection}: {collection.count()} records")
        print(f"ChromaDB: {args.persist_dir}")
        print(f"BM25: {bm25_count(bm25_db)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
