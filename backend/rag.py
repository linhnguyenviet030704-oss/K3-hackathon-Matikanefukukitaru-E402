import os
import re
from pathlib import Path
from typing import Any

import httpx

from .config import project_root


DEFAULT_CITATION = {
    "id": "placeholder-rag-source",
    "source": "DermaCare RAG",
    "title": "Placeholder Supabase pgvector retrieval",
    "year": "2026",
    "category": "Clinical Reference",
    "url": None,
    "summary": "RAG retrieval will return matched document chunks from Supabase pgvector here.",
    "evidenceLevel": "General Medical Reference",
}

RAG_COLLECTION = os.getenv("RAG_COLLECTION", "Skin")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "voyage-4")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))


def _load_voyage_api_key() -> str | None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return os.getenv("VOYAGE_API_KEY")

    root = project_root()
    load_dotenv(root / ".env")
    if not os.getenv("VOYAGE_API_KEY"):
        load_dotenv(root / "data" / ".env")
    return os.getenv("VOYAGE_API_KEY")


def _load_gemini_api_key() -> str | None:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return os.getenv("GEMINI_API_KEY")

    root = project_root()
    for path in (root / ".env", root / "backend" / ".env", root / "data" / ".env"):
        key = dotenv_values(path).get("GEMINI_API_KEY")
        if key:
            return key
    return os.getenv("GEMINI_API_KEY")


def _rag_paths() -> tuple[Path, str]:
    root = project_root()
    return Path(os.getenv("CHROMA_PERSIST_DIR", root / "data" / "chroma_db")), os.getenv("RAG_COLLECTION", RAG_COLLECTION)


def _prompt_path() -> Path:
    return Path(__file__).with_name("prompts") / "rag_answer_vi.txt"


def _citation_from_chroma(row_id: str, document: str, metadata: dict[str, Any], distance: float | None) -> dict[str, Any]:
    similarity = None if distance is None else 1.0 - float(distance)
    title = " - ".join(part for part in [metadata.get("disease"), metadata.get("section")] if part) or row_id
    summary = document.strip().replace("\n", " ")[:500]
    return {
        "id": f"rag-{row_id}",
        "documentId": row_id,
        "source": "ChromaDB Skin",
        "title": title,
        "year": "2026",
        "category": metadata.get("chapter") or "Clinical Reference",
        "url": None,
        "summary": summary,
        "evidenceLevel": f"Vector similarity {similarity:.3f}" if similarity is not None else "Vector search result",
        "metadata": {**metadata, "cosineDistance": distance, "vectorSimilarity": similarity},
    }


async def retrieve_sources(message: str | None, image_base64: str | None = None) -> list[dict[str, Any]]:
    text = (message or "").strip()
    if not text:
        citation = DEFAULT_CITATION.copy()
        if image_base64:
            citation.update(
                {
                    "id": "image-placeholder",
                    "title": "Image analysis placeholder",
                    "summary": "Image input is stored, but image embedding/vision retrieval is not implemented yet.",
                }
            )
        return [citation]

    key = _load_voyage_api_key()
    persist_dir, collection_name = _rag_paths()
    if not key or not persist_dir.exists():
        return [DEFAULT_CITATION.copy()]

    try:
        import chromadb
        import voyageai
    except ImportError:
        return [DEFAULT_CITATION.copy()]

    voyage_client = voyageai.Client(api_key=key)
    embedding = voyage_client.embed(texts=[text], model=RAG_EMBEDDING_MODEL, input_type="query", truncation=False).embeddings[0]
    collection = chromadb.PersistentClient(path=str(persist_dir)).get_collection(collection_name, embedding_function=None)
    result = collection.query(query_embeddings=[embedding], n_results=RAG_TOP_K, include=["documents", "metadatas", "distances"])
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    return [
        _citation_from_chroma(row_id, document, metadata or {}, distance)
        for row_id, document, metadata, distance in zip(ids, documents, metadatas, distances)
    ] or [DEFAULT_CITATION.copy()]


async def retrieve_sources_placeholder(_message: str | None) -> list[dict[str, Any]]:
    return [DEFAULT_CITATION.copy()]


def build_rag_prompt(message: str | None, citations: list[dict[str, Any]], conversation_context: str = "") -> str:
    template = _prompt_path().read_text(encoding="utf-8")
    context = "\n\n".join(
        f"[{idx}] {citation.get('title') or citation.get('documentId')}\n{citation.get('summary', '')}"
        for idx, citation in enumerate(citations, start=1)
    )
    return (
        template.replace("{{QUESTION}}", (message or "").strip())
        .replace("{{CONVERSATION_CONTEXT}}", conversation_context or "Chưa có ngữ cảnh hội thoại trước đó.")
        .replace("{{CONTEXT}}", context or "Không có ngữ cảnh truy xuất mới.")
    )


async def call_llm(prompt: str) -> str | None:
    key = _load_gemini_api_key()
    if not key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, params={"key": key}, json=payload)
    response.raise_for_status()
    data = response.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip() or None


def _diagnosis_from_title(title: str | None) -> str:
    diagnosis = (title or "tình trạng da trong tài liệu").split(" - ", 1)[0].strip()
    return diagnosis.lower() or "tình trạng da trong tài liệu"


def _summary_points(summary: str, diagnosis: str) -> list[str]:
    text = " ".join(summary.split())
    text = re.sub(rf"^{re.escape(diagnosis)}\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(chẩn đoán\s*)?[\d. ]*(triệu chứng lâm sàng)?\s*", "", text, flags=re.IGNORECASE)
    parts = re.split(r"\s+-\s+|(?<=[.!?])\s+", text)
    points = [part.strip(" .;-") for part in parts if len(part.strip(" .;-")) > 20]
    return points[:3] or [summary[:300].strip()]


def fallback_rag_answer(_message: str | None, citations: list[dict[str, Any]]) -> str:
    real_citations = [citation for citation in citations if citation.get("source") == "ChromaDB Skin"]
    if real_citations:
        top = real_citations[0]
        diagnosis = _diagnosis_from_title(top.get("title"))
        points = _summary_points(top.get("summary", ""), diagnosis)
        why = "\n".join(f"- {point}." for point in points)
        return (
            f"Dựa trên mô tả của bạn và tài liệu tìm được, hướng phù hợp nhất là {diagnosis}. "
            "Cần khám trực tiếp để xác nhận vì nhiều bệnh da có biểu hiện giống nhau.\n\n"
            f"Vì sao:\n{why}\n\n"
            "Nên làm gì tiếp:\n"
            "- Đặt lịch khám da liễu nếu tổn thương kéo dài, lan rộng, đau, chảy dịch hoặc ảnh hưởng sinh hoạt.\n"
            "- Tránh tự bôi corticoid/thuốc mạnh khi chưa có chỉ định.\n"
            "- Chụp lại vùng tổn thương và ghi thời điểm xuất hiện, vị trí, mức ngứa/đau để bác sĩ dễ đánh giá.\n\n"
            "Nội dung này chỉ để tham khảo và không thay thế chẩn đoán trực tiếp từ bác sĩ da liễu."
        )
    return (
        "Placeholder response: backend, Supabase auth, conversation storage, and source storage are wired. "
        "The real chat model and pgvector RAG retrieval can replace this function next."
    )
