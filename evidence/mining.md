# Bằng Chứng Khảo Sát Hệ Thống - DermaCare

## Phương Pháp
- Khảo sát hệ thống thông tin người dùng phải dùng hiện nay: các trang tham khảo y khoa riêng lẻ, tài liệu chuyên khoa, classifier ảnh đơn lẻ và chat AI tổng quát.
- Tìm điểm đứt gãy: thông tin rải rác, thiếu tính cộng hưởng giữa mô tả/ảnh/nguồn, và nguồn khó tìm nếu không biết từ khóa y khoa.
- Đọc `data/ingestion_report.json` để xác nhận knowledge base đã index: 100 dòng hợp lệ, 100 dòng đã thêm, Chroma collection `Skin`, BM25 index 100 tài liệu.
- Đọc `data/d1.md` và `data/d1_chunks.jsonl` để chọn nguồn y khoa có thể demo: ghẻ, lang ben, nấm da, candida, bạch biến, PIH, acne.
- Đọc code/tests để xác nhận prototype có guardrail và luồng chính.

## Kết Quả Khảo Sát Hệ Thống
| Phát hiện | Bằng chứng | Nhu cầu sản phẩm |
|---|---|---|
| Trang thông tin rải rác | AAD/Mayo/DermNet/NIH/WHO và tài liệu `data/d1.md` nằm ở nhiều nguồn/định dạng | Gom thành một câu trả lời có citation |
| Thiếu tính cộng hưởng | Search web không kết hợp ảnh + triệu chứng + ngữ cảnh hội thoại; classifier ảnh không có RAG | Kết hợp wizard triệu chứng, classifier hint, RAG và conversation context |
| Nguồn khó tìm | Người dùng phải biết từ khóa như ghẻ, lang ben, PIH, bạch biến, dermatophyte | Cho phép hỏi bằng mô tả đời thường và retrieve nguồn phù hợp |
| Rủi ro hiểu nhầm cao | Kết quả classifier/chat tổng quát dễ bị đọc như chẩn đoán | Guardrail: thông tin giáo dục, không kê đơn, khuyên khám khi cần |

## Bằng Chứng Đếm Được Trong Repo
| Bằng chứng | File | Số lượng |
|---|---|---:|
| Đoạn tài liệu da liễu đã index | `data/ingestion_report.json` | 100 |
| Token nguồn đã index | `data/ingestion_report.json` | 73.628 |
| Ca mẫu trong UI | `frontend/src/data/sampleCases.ts` | 5 |
| Test API backend | `backend/tests/test_api.py` | 12 |
| Test skin classifier | `backend/tests/test_skin_classifier.py` | 2 |

## Năm Ví Dụ Ngắn Từ Source Pack
- `data/d1.md`: Ghẻ có tín hiệu ngứa về đêm và nhiều người cùng gia đình có biểu hiện tương tự.
- `data/d1.md`: Lang ben có dát/mảng tròn hoặc bầu dục màu hồng, nâu hoặc trắng và có thể tái phát.
- `data/d1.md`: Nấm da do dermatophyte có thể tạo mảng đỏ hình tròn, có vảy và lan ra ngoài.
- `data/d1.md`: Bạch biến có mảng mất sắc tố giới hạn rõ, thường không ngứa và không đau.
- `data/d1.md`: Trứng cá ảnh hưởng tới thẩm mỹ, tâm lý và sự tự tin, không chỉ là tổn thương da.

## R6 Validation Với Người Dùng
Validation với người dùng sẽ được điền sau trong `validation/feedback-log.md`. Phần này được tách riêng khỏi bằng chứng khảo sát hệ thống.
