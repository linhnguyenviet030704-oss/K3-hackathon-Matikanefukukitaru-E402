import re
from typing import Any


OFF_TOPIC_RESPONSE = (
    "Mình chỉ hỗ trợ câu hỏi thuộc phạm vi da liễu như triệu chứng da, tóc, móng, phát ban, ngứa, mụn, "
    "vảy nến, ghẻ, nấm da hoặc cách chuẩn bị thông tin để đi khám da liễu. "
    "Bạn có thể mô tả vấn đề da liễu cụ thể để mình hỗ trợ an toàn hơn."
)

DERMATOLOGY_KEYWORDS = {
    "abcde", "acne", "ban", "bong", "chàm", "corticoid", "da", "dermat", "dị ứng", "đỏ", "eczema",
    "ghẻ", "herpes", "itch", "kẽ", "khô", "lang ben", "mụn", "mề đay", "mole", "móng", "nấm", "ngứa",
    "nốt ruồi", "phát ban", "psoriasis", "rash", "sẩn", "scar", "skin", "sẹo", "tóc", "tổn thương",
    "viêm da", "vảy", "vảy nến", "zona", "sắc tố", "bạch biến", "nám", "tàn nhang", "đồi mồi",
}

MEDICALISH_KEYWORDS = {
    "bệnh", "chẩn đoán", "dấu hiệu", "đặc điểm", "điều trị", "khám", "lâm sàng", "nguyên nhân",
    "phòng", "rối loạn", "triệu chứng",
}

OFF_TOPIC_KEYWORDS = {
    "bitcoin", "bóng đá", "code", "cổ phiếu", "du lịch", "giá vàng", "javascript", "python",
    "thời tiết", "thơ", "tin tức", "toán", "vé máy bay", "weather",
}

FOLLOW_UP_MARKERS = {
    "bệnh này", "cái này", "điều này", "nó", "vậy", "như vậy", "điều trị", "nên làm gì",
    "có nguy hiểm", "có lây", "nguyên nhân", "triệu chứng", "phòng tránh",
}


def latest_citations(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for message in reversed(messages):
        citations = message.get("citations")
        if message.get("role") == "assistant" and citations:
            return citations
    return []


def _tokens(text: str) -> set[str]:
    stop = {"benh", "bệnh", "nay", "này", "toi", "tôi", "ban", "bạn", "la", "là", "co", "có", "gi", "gì"}
    return {token for token in re.findall(r"[\wÀ-ỹ]+", text.lower()) if len(token) >= 3 and token not in stop}


def build_conversation_context(messages: list[dict[str, Any]], history: list[dict[str, Any]] | None = None) -> str:
    source = messages or history or []
    lines = []
    for message in source:
        role = "Người dùng" if message.get("role") == "user" else "Trợ lý"
        content = " ".join(str(message.get("content") or "").split())
        if content:
            lines.append(f"{role}: {content[:700]}")
    return "\n".join(lines[-20:])


def _context_text(messages: list[dict[str, Any]]) -> str:
    citations = latest_citations(messages)
    chunks = [citation.get("title", "") + " " + citation.get("summary", "") for citation in citations]
    chunks.extend(str(message.get("content") or "") for message in messages[-4:] if message.get("role") == "assistant")
    return " ".join(chunks)


def should_reuse_existing_context(message: str | None, previous_messages: list[dict[str, Any]]) -> bool:
    if not latest_citations(previous_messages):
        return False
    text = (message or "").lower()
    if any(marker in text for marker in FOLLOW_UP_MARKERS):
        return True
    question_tokens = _tokens(text)
    if not question_tokens:
        return False
    overlap = question_tokens & _tokens(_context_text(previous_messages))
    return len(overlap) / max(len(question_tokens), 1) >= 0.35


def is_dermatology_related(
    message: str | None,
    image_base64: str | None,
    symptom_summary: dict[str, Any] | None,
    previous_messages: list[dict[str, Any]] | None = None,
) -> bool:
    if image_base64 or symptom_summary:
        return True
    text = (message or "").lower()
    if any(keyword in text for keyword in DERMATOLOGY_KEYWORDS):
        return True
    if any(keyword in text for keyword in OFF_TOPIC_KEYWORDS):
        return False
    if any(keyword in text for keyword in MEDICALISH_KEYWORDS):
        return True
    return bool(previous_messages and should_reuse_existing_context(message, previous_messages))


def retrieval_query(message: str | None, conversation_context: str) -> str:
    if not conversation_context:
        return (message or "").strip()
    return f"{conversation_context}\nNgười dùng hỏi tiếp: {(message or '').strip()}"[-4000:]
