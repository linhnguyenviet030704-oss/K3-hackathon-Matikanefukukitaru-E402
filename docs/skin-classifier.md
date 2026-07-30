# Skin Classifier

Thư mục này chứa service và script inference cho mô hình phân loại ảnh bệnh da.

## Nội Dung Chính

- `server.py`: FastAPI service, endpoint `/predict`.
- `inference.py`: chạy inference trực tiếp trên một ảnh hoặc thư mục ảnh.
- `hf_download.py`: tải checkpoint từ Hugging Face nếu cần.
- `weights/`: nơi đặt checkpoint `*_best.pth`.
- `requirements.txt`: dependencies Python.

## Chạy Service

```bash
uvicorn server:app --host 0.0.0.0 --port 8001
```

Backend dùng biến môi trường:

```bash
CLASSIFIER_URL=http://localhost:8001/predict
```

## Chạy Suy Luận Trực Tiếp

```bash
python inference.py --model resnet50 --input path/to/photo.jpg --weights-dir weights --topk 3
```

## Ghi Chú An Toàn

- Kết quả classifier chỉ là shortlist hỗ trợ, không phải chẩn đoán.
- Câu trả lời cuối của DermaCare vẫn phải đi qua RAG, guardrail và disclaimer y tế.
- Checkpoint nên được tải từ nguồn nhóm tin cậy.
