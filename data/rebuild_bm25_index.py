from __future__ import annotations

import argparse
import gc
import json
import os
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path

from skin_index import check_fts5, chroma_page, get_chroma_collection, project_root, configure_stdio, utc_now


def rebuild(collection, bm25_db: Path) -> int:
    bm25_db.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="search_index.", suffix=".sqlite3", dir=bm25_db.parent)
    os.close(fd)
    tmp_db = Path(tmp_name)
    try:
        check_fts5()
        total = 0
        with closing(sqlite3.connect(tmp_db)) as con:
            con.execute(
                """
                CREATE TABLE chunks (
                    id TEXT PRIMARY KEY,
                    document TEXT NOT NULL,
                    metadata_json TEXT,
                    content_hash TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE VIRTUAL TABLE chunks_fts USING fts5(
                    id UNINDEXED,
                    document,
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )
            for row_id, document, metadata in chroma_page(collection):
                con.execute(
                    "INSERT INTO chunks(id, document, metadata_json, content_hash, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (row_id, document, json.dumps(metadata, ensure_ascii=False, sort_keys=True), metadata.get("_content_hash", ""), utc_now()),
                )
                con.execute("INSERT INTO chunks_fts(id, document) VALUES (?, ?)", (row_id, document))
                total += 1
            indexed = int(con.execute("SELECT count(*) FROM chunks").fetchone()[0])
            if total != collection.count() or indexed != total:
                raise SystemExit("Chroma record count khác BM25 indexed document count.")
            con.commit()
        gc.collect()
        if bm25_db.exists():
            with closing(sqlite3.connect(bm25_db)) as con:
                con.execute("PRAGMA wal_checkpoint(FULL)")
                con.execute("PRAGMA journal_mode=DELETE")
        for attempt in range(10):
            try:
                os.replace(tmp_db, bm25_db)
                break
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.5)
        return total
    except Exception:
        try:
            tmp_db.unlink(missing_ok=True)
        except PermissionError:
            pass
        raise


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="Skin")
    parser.add_argument("--persist-dir", type=Path, default=project_root() / "data" / "chroma_db")
    parser.add_argument("--bm25-db", type=Path, default=project_root() / "data" / "search_index.sqlite3")
    args = parser.parse_args()
    collection = get_chroma_collection(args.persist_dir, args.collection)
    total = rebuild(collection, args.bm25_db)
    print(f"Rebuilt BM25 index: {total} documents at {args.bm25_db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
