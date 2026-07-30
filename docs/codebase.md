# Chỉ Mục Codebase

Prototype source được giữ ở các thư mục hiện có thay vì copy trùng vào đây:

- `frontend/`: UI chat React, upload ảnh, wizard triệu chứng, citations sidebar, auth flow.
- `backend/`: API chat FastAPI, RAG prompt, guardrails, storage, tests.
- `skin-classifier/`: service FastAPI cho classifier và entry point inference local.
- `data/`: source chunks da liễu, index Chroma/BM25, scripts ingestion.
- `docker-compose.yml`: chạy classifier, backend và frontend cùng nhau.

Chạy:
```bash
docker compose up --build
```

Kiểm thử local:
```bash
python -m pytest backend/tests
cd frontend && npm run lint
```
