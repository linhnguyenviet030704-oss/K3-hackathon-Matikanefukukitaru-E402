# Demo Slides - DermaCare

## 1. Người Dùng & Công Việc
- Người dùng: người có vấn đề da nhẹ/vừa trước khi tự điều trị hoặc đặt lịch khám.
- Công việc: hiểu mức độ đáng lo và chuẩn bị thông tin đúng để trao đổi với bác sĩ.
- Bằng chứng: nguồn da liễu rải rác, thiếu cộng hưởng ảnh/triệu chứng/nguồn, nguồn khó tìm.

## 2. Vì Sao Chọn Lát Cắt Này
- Chọn: câu trả lời da liễu ban đầu an toàn, có citation.
- Loại: tóm tắt cho bác sĩ làm lát cắt chính; chỉ hữu ích sau khi đã chat.
- Loại: chia sẻ ca bệnh public; rủi ro riêng tư cao hơn.

## 3. Giải Pháp & Demo Trực Tiếp
- Lát cắt: ảnh/triệu chứng/câu hỏi -> quyết định AI conditional -> câu trả lời giáo dục có nguồn.
- Demo case chuẩn: ngứa về đêm, mụn nước ở kẽ ngón tay.
- Demo case khó: câu hỏi ngoài phạm vi hoặc yêu cầu liều thuốc.

## 4. Kết Quả Đánh Giá
- Ngưỡng chất lượng: >=80% đạt, 0 lỗi an toàn nghiêm trọng.
- Bộ case chuẩn: 24 case phủ case thường, nguồn sự thật, mơ hồ, ngoài phạm vi, rủi ro domain.
- Lượt 01: đa số kiểm tra code/prompt đạt; các dòng chạy thật LLM/ảnh cần rà thêm.

## 5. Validation Với Người Dùng
- Cần cho R6: 5 người ngoài nhóm, 3 câu hỏi, log quote nguyên văn.
- Hiện tại: template đã sẵn trong `validation/feedback-log.md`.
- Sẽ điền sau khi validation thật.

## 6. Nếu Có Thêm Một Tuần
- Thêm trace chạy thật với `GEMINI_API_KEY` cho toàn bộ golden set.
- Điền R6 validation với 5 người dùng và cập nhật changelog.
- Siết trải nghiệm khi độ tin cậy thấp nếu người dùng muốn hệ thống hỏi thêm trước khi trả lời.
