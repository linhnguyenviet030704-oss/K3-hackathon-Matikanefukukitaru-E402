import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skin_index import bm25_count, bm25_search, ensure_bm25_db, upsert_bm25


def test_bm25_persists_and_ranks_vietnamese_text(tmp_path):
    db = tmp_path / "search.sqlite3"
    ensure_bm25_db(db)
    upsert_bm25(
        db,
        [
            ("a", "Benh choc lo do vi khuan gay ra", {"disease": "A"}, "h1"),
            ("b", "Viem da co dia gay ngua va kho da", {"disease": "B"}, "h2"),
            ("c", "Dieu tri nhiem khuan da bang khang sinh", {"disease": "C"}, "h3"),
        ],
    )

    rows = bm25_search(db, "choc lo", 10)

    assert bm25_count(db) == 3
    assert rows[0]["id"] == "a"
    assert rows[0]["scores"]["bm25_raw"] > 0


def test_fts5_is_required(tmp_path):
    db = tmp_path / "search.sqlite3"
    ensure_bm25_db(db)
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT count(*) FROM chunks_fts").fetchone()[0] == 0
