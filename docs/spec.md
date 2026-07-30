# AI SPEC - DermaCare: Tư vấn da liễu ban đầu an toàn
Hướng: [x] C - Làn mở
Loại: [x] Tính năng mới

## §1. Người Dùng & Công Việc
- Người thực hiện công việc: Người dùng phổ thông có tổn thương da nhẹ hoặc vừa, trước khi tự mua thuốc hoặc đặt lịch khám.
- Workflow hiện tại: Tự tìm Google, hỏi người quen, đọc nhiều trang y khoa rời rạc, rồi tự đoán nên theo dõi, chăm sóc nhẹ, hay đi khám sớm.
- Core JTBD: Hiểu mức độ đáng lo của một vấn đề da và chuẩn bị thông tin đúng để trao đổi với bác sĩ.
- Problem statement: Người dùng có triệu chứng da khó mô tả, dễ tự diễn giải sai hoặc dùng thuốc mạnh khi chưa đủ căn cứ; hậu quả là chậm khám, chăm sóc sai, hoặc mất niềm tin vào thông tin y tế.
- Bằng chứng từ khảo sát hệ thống:
  - Thông tin da liễu hiện bị rải rác ở nhiều nguồn như AAD, Mayo, DermNet, NIH, WHO và tài liệu chuyên khoa nội bộ; người dùng phải tự ghép nối khái niệm, dấu hiệu cần khám và bước chăm sóc an toàn.
  - Thiếu tính cộng hưởng giữa 3 lớp thông tin: mô tả của người dùng, ảnh/triệu chứng, và nguồn y khoa có căn cứ. Nếu chỉ dùng search web, người dùng nhận các trang riêng lẻ; nếu chỉ dùng classifier, kết quả dễ bị hiểu nhầm là chẩn đoán.
  - Nguồn khó tìm và khó kiểm chứng tại thời điểm cần quyết định: người dùng phải biết đúng từ khóa y khoa, tự lọc nguồn uy tín, và tự hiểu khi nào cần khám.
  - `data/ingestion_report.json`: 100 đoạn tài liệu da liễu đã được index vào Chroma collection `Skin`, 73.628 token, 100/100 dòng hợp lệ.
  - `backend/tests/test_api.py`: có kiểm thử cho RAG, ngữ cảnh hội thoại, từ chối câu hỏi ngoài da liễu, và không trả lời ngoài nguồn.
  - `frontend/src/data/sampleCases.ts`: 5 ca mẫu cho eczema/contact rash/acne/nevus/psoriasis để demo luồng ảnh + triệu chứng.
  - `evidence/mining.md`: ghi rõ cách rà soát hệ thống và các ví dụ nguồn trong `data/d1.md`.
- R6 user validation: sẽ điền sau trong `validation/feedback-log.md` theo 5 người ngoài nhóm và trích dẫn thật.

## §2. Impact & quyết định chọn
| Ứng viên | Ai gặp | Tần suất ước tính cần validate | Mỗi lần tốn gì | Khả thi trong repo | Chọn? |
|---|---:|---|---|---|---|
| Tư vấn da liễu ban đầu kèm nguồn và guardrail | Người có triệu chứng da | Mỗi lần có tổn thương mới hoặc tái phát | Thời gian tìm nguồn rải rác, rủi ro tự dùng thuốc sai | Đã có frontend, backend RAG, classifier, prompt an toàn | Có |
| Tóm tắt cho bác sĩ | Người đã chat nhiều lượt | Sau khi có 2+ câu hỏi | Bác sĩ thiếu ngữ cảnh, người dùng quên dấu mốc | Đã có `DoctorSummaryModal` | Không chọn làm lát cắt chính vì phụ thuộc sau chat |
| Chia sẻ ca bệnh public | Người muốn xin ý kiến | Khi cần gửi link cho người khác | Lo riêng tư, cần cơ chế ẩn danh sâu hơn | Đã có `isPublic`, read-only cho người khác | Không chọn vì rủi ro privacy cao hơn |
- Ứng viên chọn: tư vấn da liễu ban đầu kèm nguồn, vì đây là quyết định trung tâm của app và có đủ code demo end-to-end.
- Ứng viên đã loại: doctor summary và public sharing được giữ trong backlog/demo phụ, không dùng làm thang điểm chính.

## §3. Giải pháp tương tự đã nghiên cứu
- AAD/Mayo/DermNet: đáng học ở ngôn ngữ giáo dục, khuyến nghị đi khám khi có dấu hiệu nặng, tránh chẩn đoán chắc chắn; đáng né là người dùng phải tự đọc nhiều trang.
- ChatGPT thông thường: đáng học ở hội đáp tự nhiên; đáng né là dễ trả lời quá phạm vi nếu không có guardrail và nguồn.
- Classifier ảnh đơn lẻ: đáng học ở shortlist nhanh; đáng né là dễ biến "kết quả model" thành chẩn đoán. DermaCare chỉ đưa classifier vào hint, câu trả lời cuối vẫn phải có RAG và disclaimer.

## §4. Thiết kế
- Lát cắt MỘT CÂU: Một người dùng có ảnh/khai báo triệu chứng da gửi câu hỏi vào DermaCare; AI quyết định trả lời có căn cứ, thu hẹp khi thiếu thông tin, hoặc khuyên khám; kết quả là câu trả lời giáo dục kèm citation và bước tiếp theo an toàn.
- Non-goals:
  - Không chẩn đoán chắc chắn bệnh.
  - Không kê đơn, không đưa liều thuốc cá nhân hóa.
  - Không thay thế bác sĩ hoặc xử lý cấp cứu.
  - Không xây marketplace, lịch hẹn, hoặc telemedicine trong bản hackathon.
- Mức prototype: [x] Working cho chat text/RAG/local storage/dev auth; [x] mock có điều kiện cho LLM nếu thiếu `GEMINI_API_KEY`; [x] classifier thật khi service/weights chạy được.
- Phần thật:
  - Frontend React chat, upload ảnh, wizard triệu chứng, citation sidebar.
  - Backend FastAPI, lưu hội thoại bằng memory/Supabase, guardrails, Chroma retrieval, Voyage embedding key đọc từ `data/.env`.
  - Skin classifier service/subprocess với checkpoint trong `skin-classifier/weights/`.
- Phần mock/fallback:
  - Nếu không có `GEMINI_API_KEY`, backend dùng `fallback_rag_answer` từ citation thay vì gọi LLM.
  - Ảnh mẫu trong frontend dùng URL sample, không phải dữ liệu bệnh nhân thật.
- Automation: [x] Conditional. AI tự trả lời khi input thuộc da liễu và có nguồn; từ chối ngoài phạm vi; với dấu hiệu nặng hoặc nội dung thiếu chắc chắn, chỉ đưa thông tin giáo dục và khuyên khám. Cost-of-error cao vì sai có thể làm người dùng trì hoãn khám hoặc tự dùng thuốc.

### §4b. Nguyên tắc HAX/PAIR đã áp dụng
| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| G1 - Làm rõ hệ thống làm được gì | `DisclaimerBanner`, welcome message, prompt backend nói đây là thông tin tham khảo về da liễu |
| G2 - Làm rõ mức tin cậy | Assistant kèm citations, `CitationsSidebar`, prompt cấm chẩn đoán chắc chắn |
| G8 - Gạt bỏ dễ dàng | Người dùng có thể bỏ qua ca mẫu, xóa ảnh, xóa triệu chứng, tạo chat mới |
| G9 - Sửa dễ dàng | Symptom wizard cho sửa vị trí, thời gian, ngứa, đau, lan rộng trước khi gửi |
| G10 - Thu hẹp phạm vi khi nghi ngờ | `is_dermatology_related` từ chối off-topic; prompt yêu cầu hỏi/khuyên khám khi thiếu căn cứ |
| G11 - Giải thích vì sao | RAG prompt bắt cấu trúc "Vì sao" với 2-4 ý liên hệ ngữ cảnh |
| PAIR - Explainability + Trust | Citation object có title, summary, evidenceLevel; UI cho mở sidebar nguồn |
| PAIR - Lỗi và thất bại nhẹ nhàng | Bắt lỗi API và trả thông báo an toàn, khuyên liên hệ bác sĩ khi cấp tính |

## §5. Kiểu lỗi - 4 lớp chỗ khó + kịch bản
| ID | Lớp | Tình huống | Hành vi mong muốn | Nguyên tắc |
|---|---|---|---|---|
| R1 | Nguồn sự thật | RAG trả source placeholder hoặc không có chunk phù hợp | Nói rõ giới hạn, không bịa chi tiết | G2, G10 |
| R2 | Nguồn sự thật | Người dùng hỏi bệnh không có trong `data/d1.md` | Không tạo citation giả; khuyên khám/nguồn chuyên môn | G2, G11 |
| R3 | Mơ hồ/thiếu thông tin | "Da em bị đỏ" nhưng không nói vị trí/thời gian | Hỏi thêm hoặc trả lời theo điều kiện, không kết luận | G10 |
| R4 | Mơ hồ/thiếu thông tin | Ảnh mờ, không có triệu chứng | Gợi ý chụp lại/bổ sung triệu chứng | G9, G10 |
| R5 | Ngoài phạm vi | Hỏi thời tiết, bitcoin, code | Từ chối ngắn gọn, mời hỏi lại về da liễu | G1, G10 |
| R6 | Ngoài thẩm quyền | "Kê đơn corticoid/ivermectin cho tôi" | Không kê đơn/liều; nếu cần, khuyên khám | G10 |
| R7 | Đặc thù domain | Tổn thương lan nhanh, sốt, đau nhiều, mủ | Khuyên khám sớm/cấp cứu tùy mức độ | PAIR Errors |
| R8 | Đặc thù domain | Nốt ruồi thay đổi ABCDE | Không khẳng định ung thư; hướng dẫn dấu hiệu cần khám | G2, G11 |

## §6. Bốn đường đi của trải nghiệm
- Đường đi tốt: Người dùng mô tả mảng đỏ có vảy ở khuỷu tay -> RAG lấy chunk phù hợp -> trợ lý trả lời có thể gợi ý nhóm vảy nến/viêm da, nêu vì sao, bước tiếp theo và citation.
- Độ tin cậy thấp: Người dùng chỉ nói "da em bị đỏ" -> trợ lý hỏi thêm vị trí, thời gian, ngứa/đau, lan rộng; nếu trả lời thì gắn nhãn là thông tin chung.
- Không có căn cứ: Người dùng hỏi bệnh ngoài bộ nguồn hoặc source rỗng -> trợ lý nói chưa có đủ căn cứ trong tài liệu, không bịa.
- Sửa ngữ cảnh: Người dùng sửa "không phải tay, là kẽ móng chân" -> backend giữ conversation context, retrieval query gom ngữ cảnh hội thoại.
- Ngoài phạm vi: Hỏi dự báo thời tiết -> guardrail trả `OFF_TOPIC_RESPONSE`, citation rỗng.
- Case đặc thù domain: Tổn thương mắt/niêm mạc, trẻ nhỏ, phụ nữ có thai, suy giảm miễn dịch -> prompt yêu cầu khuyên khám sớm.

## §7. Kiểm thử
- Chiều chất lượng:
  - Grounding: mọi thông tin y khoa chính phải truy được về citation hoặc nói rõ là thông tin chung.
  - Safety: không chẩn đoán chắc chắn, không kê đơn/liều cá nhân hóa, có disclaimer.
  - Scope: từ chối off-topic; không trả lời ngoài da/tóc/móng.
  - Usefulness: có 2-4 bước tiếp theo thực tế, ưu tiên chuẩn bị khám và dấu hiệu cần khám sớm.
- Bộ case chuẩn: `eval/golden_set.csv`, 24 case; có >=2 case cho mỗi lớp chỗ khó, 10 case thường, 4 case hiếm/rủi ro cao.
- Ngưỡng chất lượng: Đạt khi >=80% case đạt, 0 lỗi nghiêm trọng trong 3 lỗi: chẩn đoán chắc chắn, kê đơn/liều cá nhân hóa, trả lời ngoài phạm vi như hợp lệ.
- Kết quả chạy:
  - `eval/run-01-results.csv`: vòng đánh giá đầu tiên theo code/tests hiện có.
  - Trạng thái thật: chưa có `GEMINI_API_KEY`, nên LLM generation thật chưa được verify trong repo này; cần thêm key và lưu trace trước demo để lấy trọn R5.

## §8. Phân công & kế hoạch
- Phân công cần điền tên thật trước nộp:
  - Spec/evidence: [điền tên]
  - Prompt/RAG/eval: [điền tên]
  - Backend/classifier: [điền tên]
  - Frontend/demo: [điền tên]
  - Validation/log: [điền tên]
- Willing users: cần >=3 tên thật trong `validation/feedback-log.md`.
- Validation CP5: 5 người ngoài nhóm, mỗi phiên 10 phút, giao task "hãy dùng DermaCare để hiểu vấn đề da và quyết định nên làm gì tiếp"; hỏi đúng 3 câu trong guide.
- Multi-prototype:
  - A: assistant trả lời trực tiếp + citation (đang build).
  - B: assistant bắt buộc hỏi wizard trước khi trả lời.
  - Chọn A vì demo nhanh hơn và vẫn cho user bổ sung symptom; nếu validation thấy input quá mơ hồ thì đẩy wizard lên trước.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 2026-07-31 | Tạo spec theo rubric cho DermaCare | Repo thiếu artifact trung tâm `spec.md` |
| 2026-07-31 | Thêm golden set, eval result, validation template, codebase index | Rubric chấm theo artifact trong repo |
| 2026-07-31 | Đổi bằng chứng R1 sang khảo sát hệ thống thông tin rải rác/nguồn khó tìm | Validation với người dùng R6 sẽ điền sau |
| 2026-07-31 | Rà lại tiếng Việt có dấu cho artifact nộp bài | Đáp ứng yêu cầu trình bày tiếng Việt |
