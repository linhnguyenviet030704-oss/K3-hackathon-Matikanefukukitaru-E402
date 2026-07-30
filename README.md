# Mini Hackathon AI - Batch 03

## Bản Đồ Nộp Bài DermaCare

Prototype hiện tại: DermaCare, trợ lý thông tin da liễu với UI React, backend FastAPI, RAG citations, guardrails và service phân loại ảnh da.

Artifact chấm điểm:

| Artifact | Mục đích |
|---|---|
| `spec.md` | AI spec bám rubric |
| `evidence/mining.md` | Bằng chứng khảo sát hệ thống: nguồn rải rác, thiếu cộng hưởng, nguồn khó tìm |
| `eval/golden_set.csv` | Bộ case chuẩn 24 case |
| `eval/run-01-results.csv` | Kết quả đánh giá lượt 1 |
| `validation/feedback-log.md` | Mẫu log validation với người dùng cho R6 |
| `docs/codebase-README.md` | Chỉ mục tới các thư mục prototype thật |
| `docs/reflection-README.md` | Mẫu reflection cho từng thành viên |

Trước khi nộp cuối, điền tên thành viên thật và quote user validation R6 trong `validation/feedback-log.md`.

## Cách Chạy Nhanh

```bash
docker compose up --build
```

Hoặc chạy kiểm thử local:

```bash
python -m pytest backend/tests
cd frontend && npm run lint
```

## Cấu Trúc Chính

```text
repo/
├── spec.md
├── demo-slides.pdf
├── demo-slides.md
├── docs/
├── evidence/
├── eval/
├── validation/
├── reflection/
├── backend/
├── frontend/
├── skin-classifier/
├── data/
└── docker-compose.yml
```

## Ghi Chú Chấm Điểm

- Rubric chấm chuỗi quyết định và bằng chứng, không chấm độ hoành tráng của sản phẩm.
- Kết quả đánh giá phải ghi trung thực, kể cả case chưa đạt hoặc cần rà khi chạy thật.
- R6 cần 5 người ngoài nhóm, quote nguyên văn và thay đổi/changelog từ feedback.
- Không commit API key.
- Dữ liệu trong `data/` chỉ dùng trong phạm vi hackathon và không chia sẻ ra ngoài khóa học.
