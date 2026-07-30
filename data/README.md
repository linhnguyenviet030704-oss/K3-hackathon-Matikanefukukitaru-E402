# Ingestion và tìm kiếm Skin

## Cài đặt

Windows PowerShell:

```powershell
py -3.14 -m venv data\.venv
data\.venv\Scripts\python.exe -m pip install -r data\requirements.txt
```

Linux/macOS:

```bash
python3 -m venv data/.venv
data/.venv/bin/python -m pip install -r data/requirements.txt
```

Đặt `VOYAGE_API_KEY` trong `.env` ở project root. Repository hiện có thể đọc fallback `data/.env` nếu root `.env` chưa tồn tại.

## Ingestion

Dry-run:

```powershell
data\.venv\Scripts\python.exe data\embed_jsonl_to_chroma.py --input data\d1_chunks.jsonl --dry-run
```

Chạy thật:

```powershell
data\.venv\Scripts\python.exe data\embed_jsonl_to_chroma.py --input data\d1_chunks.jsonl --collection Skin --persist-dir data\chroma_db
```

Chạy lại sau gián đoạn dùng cùng lệnh. Script kiểm tra ID và `_content_hash`, bỏ qua record không đổi, sửa BM25 nếu thiếu, và không tạo duplicate.

ChromaDB nằm ở `data/chroma_db`, collection là `"Skin"`, document embedding dùng `voyage-4` với `input_type="document"`. Vector được lưu bằng HNSW cosine. Rate limit embedding dùng rolling window 60 giây với 10.000 TPM, 3 RPM, budget 9.500 token.

Kiểm tra số record:

```powershell
data\.venv\Scripts\python.exe -c "import chromadb; c=chromadb.PersistentClient(path='data/chroma_db').get_collection('Skin'); print(c.count())"
```

## BM25

BM25 persistent dùng SQLite FTS5 tại `data/search_index.sqlite3`, tokenizer `unicode61 remove_diacritics 2`. Rebuild từ ChromaDB:

```powershell
data\.venv\Scripts\python.exe data\rebuild_bm25_index.py --collection Skin --persist-dir data\chroma_db --bm25-db data\search_index.sqlite3
```

Nếu ChromaDB và BM25 lệch số document, chạy rebuild. Database cũ chỉ bị thay thế sau khi database tạm rebuild xong và count khớp.

## Search modes

BM25 chỉ dùng word search, không gọi API:

```powershell
data\.venv\Scripts\python.exe data\search_skin.py --query "triệu chứng nhiễm khuẩn da" --mode bm25 --top-k 10
```

Vector tạo query embedding bằng `voyage-4`, `input_type="query"`, rồi query HNSW:

```powershell
data\.venv\Scripts\python.exe data\search_skin.py --query "triệu chứng nhiễm khuẩn da" --mode vector --top-k 10
```

Hybrid lấy BM25 top 10 và vector top 10, normalize từng danh sách về `[0, 1]`, rồi tính:

```text
hybrid_score = bm25_normalized + vector_normalized
```

Không cộng trực tiếp raw BM25 với raw vector vì hai thang điểm khác nhau.

```powershell
data\.venv\Scripts\python.exe data\search_skin.py --query "triệu chứng nhiễm khuẩn da" --mode hybrid --top-k 10
```

Rerank chạy hybrid trước, lấy top candidate, rồi gọi Voyage `rerank-2.5`:

```powershell
data\.venv\Scripts\python.exe data\search_skin.py --query "triệu chứng nhiễm khuẩn da" --mode rerank --top-k 10
```

Xuất JSON:

```powershell
data\.venv\Scripts\python.exe data\search_skin.py --query "triệu chứng nhiễm khuẩn da" --mode hybrid --json
```

## Test

```powershell
data\.venv\Scripts\python.exe -m pytest data\tests -v
```
