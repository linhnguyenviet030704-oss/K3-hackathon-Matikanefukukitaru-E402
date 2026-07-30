from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sqlite3
import sys
import time
from collections import deque
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


MODEL = "voyage-4"
INPUT_TYPE_DOCUMENT = "document"
TPM_LIMIT = 10_000
RPM_LIMIT = 3
TOKEN_BUDGET = 9_500
WINDOW_SECONDS = 60
MAX_BATCH_ITEMS = 1000
TEXT_FIELDS = ("text", "content", "chunk", "document", "page_content", "chunk_text")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(row: dict, source_file: Path, line_no: int, text: str) -> str:
    for key in ("id", "chunk_id", "_id"):
        if row.get(key) is not None:
            return str(row[key])
    return sha256_text(f"{source_file.resolve()}\n{line_no}\n{text}")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_voyage_key() -> str:
    root = project_root()
    load_dotenv(root / ".env")
    if not os.getenv("VOYAGE_API_KEY"):
        load_dotenv(root / "data" / ".env")
    key = os.getenv("VOYAGE_API_KEY")
    if not key:
        raise SystemExit("Không tìm thấy VOYAGE_API_KEY trong môi trường hoặc file .env.")
    return key


def find_jsonl_input(data_dir: Path) -> Path:
    files = sorted(p for p in data_dir.glob("*.jsonl") if p.name != "failed_rows.jsonl")
    if len(files) == 1:
        return files[0]
    if not files:
        raise SystemExit("Không tìm thấy file JSONL trong data/. Hãy truyền --input.")
    raise SystemExit("Có nhiều file JSONL trong data/. Hãy truyền --input để chọn rõ ràng.")


def get_text(row: dict, text_field: str | None) -> tuple[str | None, str | None]:
    fields = (text_field,) if text_field else TEXT_FIELDS
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value, field
    return None, None


def flatten_metadata(row: dict, text_field: str, source_file: Path, line_no: int, content_hash: str, model: str) -> dict:
    raw = {}
    nested = row.get("metadata")
    if isinstance(nested, dict):
        raw.update(nested)
    for key, value in row.items():
        if key not in {text_field, "metadata"}:
            raw[key] = value

    metadata = {}
    for key, value in raw.items():
        if key.startswith("_") or value is None or key == "embedding":
            continue
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        elif isinstance(value, (dict, list)):
            metadata[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)

    metadata.update(
        {
            "_source_file": str(source_file.resolve()),
            "_source_line": line_no,
            "_content_hash": content_hash,
            "_embedding_model": model,
            "_input_type": INPUT_TYPE_DOCUMENT,
            "_embedded_at": utc_now(),
        }
    )
    return metadata


class RollingRateLimiter:
    def __init__(self, rpm: int = RPM_LIMIT, token_budget: int = TOKEN_BUDGET, window_seconds: int = WINDOW_SECONDS):
        self.rpm = rpm
        self.token_budget = token_budget
        self.window_seconds = window_seconds
        self.requests: deque[tuple[float, int]] = deque()
        self.wait_seconds = 0.0

    def wait(self, tokens: int) -> None:
        while True:
            now = time.monotonic()
            while self.requests and now - self.requests[0][0] >= self.window_seconds:
                self.requests.popleft()
            used_tokens = sum(t for _, t in self.requests)
            if len(self.requests) < self.rpm and used_tokens + tokens <= self.token_budget:
                self.requests.append((now, tokens))
                return
            wait_for = self.window_seconds - (now - self.requests[0][0]) + random.uniform(0.05, 0.5)
            time.sleep(max(wait_for, 0.05))
            self.wait_seconds += max(wait_for, 0.05)


def retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None)
    if headers and headers.get("Retry-After"):
        try:
            return float(headers["Retry-After"])
        except ValueError:
            return None
    return None


def status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None) or getattr(exc, "status_code", None)


def is_retryable(exc: Exception) -> bool:
    code = status_code(exc)
    if code in {429, 500, 502, 503, 504}:
        return True
    name = exc.__class__.__name__.lower()
    return any(word in name for word in ("ratelimit", "timeout", "connection", "network"))


def call_with_retry(fn, *, attempts: int = 8):
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            code = status_code(exc)
            if code in {401, 403}:
                raise SystemExit("Voyage API từ chối xác thực. Hãy kiểm tra VOYAGE_API_KEY.") from exc
            if attempt == attempts - 1 or not is_retryable(exc):
                raise
            delay = retry_after_seconds(exc)
            if delay is None:
                delay = min(60, 2**attempt) + random.uniform(0, 1)
            time.sleep(delay)
    raise RuntimeError("retry failed")


def check_fts5() -> None:
    with closing(sqlite3.connect(":memory:")) as con:
        try:
            con.execute("CREATE VIRTUAL TABLE x USING fts5(y)")
        except sqlite3.OperationalError as exc:
            raise SystemExit("Python/SQLite hiện tại không hỗ trợ FTS5. Hãy cài Python có SQLite FTS5.") from exc


def ensure_bm25_db(db_path: Path) -> None:
    check_fts5()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
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
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                id UNINDEXED,
                document,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        con.commit()


def upsert_bm25(db_path: Path, rows: list[tuple[str, str, dict, str]]) -> int:
    ensure_bm25_db(db_path)
    with closing(sqlite3.connect(db_path)) as con:
        for row_id, document, metadata, content_hash in rows:
            metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
            con.execute(
                """
                INSERT INTO chunks(id, document, metadata_json, content_hash, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    document=excluded.document,
                    metadata_json=excluded.metadata_json,
                    content_hash=excluded.content_hash,
                    updated_at=excluded.updated_at
                """,
                (row_id, document, metadata_json, content_hash, utc_now()),
            )
            con.execute("DELETE FROM chunks_fts WHERE id = ?", (row_id,))
            con.execute("INSERT INTO chunks_fts(id, document) VALUES (?, ?)", (row_id, document))
        con.commit()
    return len(rows)


def bm25_exists(db_path: Path, row_id: str) -> bool:
    ensure_bm25_db(db_path)
    with closing(sqlite3.connect(db_path)) as con:
        return con.execute("SELECT 1 FROM chunks WHERE id = ?", (row_id,)).fetchone() is not None


def bm25_count(db_path: Path) -> int:
    ensure_bm25_db(db_path)
    with closing(sqlite3.connect(db_path)) as con:
        return int(con.execute("SELECT count(*) FROM chunks").fetchone()[0])


def fts_query(query: str) -> str:
    import re

    tokens = re.findall(r"[\w]+", query, flags=re.UNICODE)
    return " ".join(tokens)


def bm25_search(db_path: Path, query: str, limit: int) -> list[dict]:
    ensure_bm25_db(db_path)
    match = fts_query(query)
    if not match:
        return []
    with closing(sqlite3.connect(db_path)) as con:
        rows = con.execute(
            """
            SELECT c.id, c.document, c.metadata_json, bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.id
            WHERE chunks_fts MATCH ?
            ORDER BY score ASC
            LIMIT ?
            """,
            (match, limit),
        ).fetchall()
    out = []
    for rank, (row_id, document, metadata_json, raw_score) in enumerate(rows, start=1):
        metadata = json.loads(metadata_json) if metadata_json else {}
        out.append(
            {
                "rank": rank,
                "id": row_id,
                "document": document,
                "metadata": metadata,
                "source_ranks": {"bm25": rank, "vector": None},
                "scores": {
                    "bm25_raw": -float(raw_score),
                    "bm25_normalized": None,
                    "cosine_distance": None,
                    "vector_similarity": None,
                    "vector_normalized": None,
                    "hybrid": None,
                    "reranker": None,
                },
            }
        )
    return out


def hnsw_metadata(ef_construction: int, ef_search: int, max_neighbors: int, model: str = MODEL) -> dict:
    return {
        "hnsw:space": "cosine",
        "hnsw:construction_ef": ef_construction,
        "hnsw:search_ef": ef_search,
        "hnsw:M": max_neighbors,
        "embedding_model": model,
    }


def get_chroma_collection(persist_dir: Path, name: str, ef_construction: int = 200, ef_search: int = 100, max_neighbors: int = 32, model: str = MODEL, rebuild_hnsw: bool = False):
    import chromadb

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    metadata = hnsw_metadata(ef_construction, ef_search, max_neighbors, model)
    try:
        collection = client.get_collection(name=name, embedding_function=None)
        existing = collection.metadata or {}
        if not existing:
            collection.modify(metadata={"embedding_model": model})
            existing = collection.metadata or {}
        config = getattr(collection, "configuration", {}) or {}
        hnsw = config.get("hnsw") or {}
        space = hnsw.get("space") or existing.get("hnsw:space")
        if space not in (None, "cosine"):
            if not rebuild_hnsw:
                raise SystemExit("Collection Skin không dùng cosine. Chạy lại với --rebuild-hnsw để tạo lại sau khi sao lưu.")
            backup = persist_dir.with_name(f"{persist_dir.name}_backup_{int(time.time())}")
            shutil.copytree(persist_dir, backup)
            client.delete_collection(name)
            collection = client.create_collection(name=name, embedding_function=None, metadata=metadata)
        return collection
    except Exception as exc:
        if exc.__class__.__name__ not in {"NotFoundError", "InvalidCollectionException"} and "does not exist" not in str(exc):
            raise

    try:
        return client.create_collection(
            name=name,
            embedding_function=None,
            metadata=metadata,
            configuration={
                "hnsw": {
                    "space": "cosine",
                    "ef_construction": ef_construction,
                    "ef_search": ef_search,
                    "max_neighbors": max_neighbors,
                    "batch_size": 100,
                    "sync_threshold": 1000,
                }
            },
        )
    except TypeError:
        return client.create_collection(name=name, embedding_function=None, metadata=metadata)


def collection_get_existing(collection, row_id: str) -> tuple[dict | None, str | None]:
    got = collection.get(ids=[row_id], include=["metadatas", "documents"])
    ids = got.get("ids") or []
    if not ids:
        return None, None
    metadata = (got.get("metadatas") or [{}])[0] or {}
    document = (got.get("documents") or [None])[0]
    return metadata, document


def chroma_page(collection, limit: int = 500):
    offset = 0
    while True:
        batch = collection.get(include=["documents", "metadatas"], limit=limit, offset=offset)
        ids = batch.get("ids") or []
        if not ids:
            break
        for row_id, document, metadata in zip(ids, batch.get("documents") or [], batch.get("metadatas") or []):
            yield row_id, document, metadata or {}
        offset += len(ids)
