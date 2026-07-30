import os

from fastapi.testclient import TestClient

from backend import app as app_module
from backend.app import app, memory_store


def test_chat_placeholder_persists_conversation_and_sources(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()

    async def fake_retrieve(message, image_base64=None):
        return [
            {
                "id": "placeholder-rag-source",
                "source": "DermaCare RAG",
                "title": "Placeholder retrieval",
                "year": "2026",
                "category": "Clinical Reference",
                "url": None,
                "summary": "Placeholder summary",
                "evidenceLevel": "General Medical Reference",
                "metadata": {},
            }
        ]

    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve)

    client = TestClient(app)

    created = client.post("/api/conversations", json={"title": "Rash case", "isPublic": True})
    assert created.status_code == 200
    conversation = created.json()
    assert conversation["title"] == "Rash case"
    assert conversation["isPublic"] is True

    reply = client.post(
        "/api/chat",
        json={"conversationId": conversation["id"], "message": "Itchy red rash on arm"},
    )
    assert reply.status_code == 200
    payload = reply.json()
    assert payload["conversation"]["id"] == conversation["id"]
    assert payload["citations"]

    listed = client.get("/api/conversations")
    assert listed.status_code == 200
    sessions = listed.json()
    assert sessions[0]["messages"][-1]["role"] == "assistant"
    assert sessions[0]["messages"][-1]["citations"] == payload["citations"]

    sources = client.get(f"/api/conversations/{conversation['id']}/sources")
    assert sources.status_code == 200
    assert sources.json()[0]["title"] == payload["citations"][0]["title"]


def test_chat_uses_text_rag_retrieval(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    calls = []

    async def fake_retrieve(message, image_base64=None):
        calls.append((message, image_base64))
        return [
            {
                "id": "rag-d1_0002",
                "documentId": "d1_0002",
                "source": "ChromaDB Skin",
                "title": "BỆNH GHẺ - CHẨN ĐOÁN",
                "year": "2026",
                "category": "Chương 2",
                "url": None,
                "summary": "Triệu chứng lâm sàng...",
                "evidenceLevel": "Vector similarity 0.91",
                "metadata": {"vectorSimilarity": 0.91},
            }
        ]

    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve, raising=False)
    client = TestClient(app)

    reply = client.post("/api/chat", json={"message": "triệu chứng bệnh ghẻ"})

    assert reply.status_code == 200
    payload = reply.json()
    assert calls == [("triệu chứng bệnh ghẻ", None)]
    assert payload["citations"][0]["documentId"] == "d1_0002"
    assert "Vì sao:" in payload["text"]
    assert "collection Skin" not in payload["text"]


def test_chat_runs_skin_classifier_before_image_rag(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    seen = {}

    def fake_classify(image_base64, mime_type=None):
        seen["classified"] = (image_base64, mime_type)
        return {
            "pred_class": "Acne",
            "pred_class_vi": "Mun trung ca",
            "confidence": 0.91,
            "top": [{"label": "Acne", "label_vi": "Mun trung ca", "confidence": 0.91}],
        }

    async def fake_retrieve(message, image_base64=None):
        seen["retrieve"] = (message, image_base64)
        return [
            {
                "id": "rag-acne",
                "documentId": "acne",
                "source": "ChromaDB Skin",
                "title": "ACNE - OVERVIEW",
                "summary": "Acne reference.",
                "category": "Clinical Reference",
                "evidenceLevel": "Vector similarity 0.91",
            }
        ]

    async def fake_call_llm(prompt):
        seen["prompt"] = prompt
        return "The image shortlist points to acne."

    monkeypatch.setattr(app_module, "classify_image_base64", fake_classify)
    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve)
    monkeypatch.setattr(app_module, "call_llm", fake_call_llm)
    client = TestClient(app)

    reply = client.post(
        "/api/chat",
        json={
            "message": "Anh nay la benh gi?",
            "imageBase64": "data:image/png;base64,abc",
            "mimeType": "image/png",
        },
    )

    assert reply.status_code == 200
    assert seen["classified"] == ("data:image/png;base64,abc", "image/png")
    assert "Acne" in seen["retrieve"][0]
    assert "Mun trung ca" in seen["prompt"]
    assert seen["retrieve"][1] == "data:image/png;base64,abc"
    payload = reply.json()
    assert payload["citations"][0]["documentId"] == "acne"
    assert "Classifier ảnh" in payload["text"]
    assert "Mun trung ca / Acne (91%)" in payload["text"]


def test_fallback_rag_answer_is_user_friendly():
    text = app_module.fallback_rag_answer(
        "Mảng đỏ vảy trắng bạc ở khuỷu tay và đầu gối",
        [
            {
                "source": "ChromaDB Skin",
                "title": "VẢY NẾN THỂ THÔNG THƯỜNG - 2. CHẨN ĐOÁN",
                "summary": "VẢY NẾN THỂ THÔNG THƯỜNG CHẨN ĐOÁN 2.1 Triệu chứng lâm sàng - Tổn thương da: điển hình là những sẩn, mảng màu đỏ tươi, giới hạn rõ với da lành, trên có vảy da trắng, dày, dễ bong. Vị trí thường ở chỗ tỳ đè, vùng hay bị cọ xát như khuỷu tay, đầu gối.",
            }
        ],
    )

    assert "vảy nến thể thông thường" in text.lower()
    assert "Vì sao:" in text
    assert "Nên làm gì tiếp:" in text
    assert "collection Skin" not in text


def test_dev_auth_token_separates_conversation_history(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    client = TestClient(app)

    created = client.post(
        "/api/conversations",
        json={"title": "User A case"},
        headers={"Authorization": "Bearer dev-user-a"},
    )

    assert created.status_code == 200
    assert client.get("/api/conversations", headers={"Authorization": "Bearer dev-user-a"}).json()
    assert client.get("/api/conversations", headers={"Authorization": "Bearer dev-user-b"}).json() == []


def test_public_conversation_is_read_only_for_other_user(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    client = TestClient(app)

    created = client.post(
        "/api/conversations",
        json={"title": "Public case", "isPublic": True},
        headers={"Authorization": "Bearer dev-owner"},
    ).json()

    other_headers = {"Authorization": "Bearer dev-other"}
    listed = client.get("/api/conversations", headers=other_headers).json()

    assert listed[0]["id"] == created["id"]
    assert client.patch(f"/api/conversations/{created['id']}", json={"title": "Nope"}, headers=other_headers).status_code == 403
    assert client.delete(f"/api/conversations/{created['id']}", headers=other_headers).status_code == 403


def test_chat_reuses_existing_context_without_second_retrieval(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    calls = []

    async def fake_retrieve(message, image_base64=None):
        calls.append(message)
        return [
            {
                "id": "rag-psoriasis",
                "documentId": "psoriasis",
                "source": "ChromaDB Skin",
                "title": "VẢY NẾN THỂ THÔNG THƯỜNG - 2. CHẨN ĐOÁN",
                "summary": "Tổn thương da là mảng đỏ giới hạn rõ, có vảy trắng bạc ở khuỷu tay và đầu gối.",
                "category": "Clinical Reference",
                "evidenceLevel": "Vector similarity 0.91",
            }
        ]

    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve)
    client = TestClient(app)
    first = client.post("/api/chat", json={"message": "Mảng đỏ vảy trắng bạc ở khuỷu tay là bệnh gì?"}).json()
    conversation_id = first["conversation"]["id"]
    second = client.post(
        "/api/chat",
        json={"conversationId": conversation_id, "message": "Bệnh này nên làm gì tiếp?"},
    ).json()

    assert len(calls) == 1
    assert second["citations"][0]["documentId"] == "psoriasis"


def test_chat_rejects_non_dermatology_without_retrieval(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()

    async def fail_retrieve(message, image_base64=None):
        raise AssertionError("off-topic question should not hit vector search")

    monkeypatch.setattr(app_module, "retrieve_sources", fail_retrieve)
    client = TestClient(app)

    reply = client.post("/api/chat", json={"message": "Dự báo thời tiết hôm nay thế nào?"})

    assert reply.status_code == 200
    payload = reply.json()
    assert payload["citations"] == []
    assert "da liễu" in payload["text"].lower()


def test_pigment_disorder_question_hits_retrieval(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    calls = []

    async def fake_retrieve(message, image_base64=None):
        calls.append(message)
        return [
            {
                "id": "rag-pigment",
                "documentId": "pigment",
                "source": "ChromaDB Skin",
                "title": "RỐI LOẠN SẮC TỐ - TỔNG QUAN",
                "summary": "Rối loạn sắc tố gồm tăng sắc tố, giảm sắc tố và mất sắc tố.",
                "category": "Clinical Reference",
                "evidenceLevel": "Vector similarity 0.90",
            }
        ]

    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve)
    client = TestClient(app)

    reply = client.post("/api/chat", json={"message": "Các bệnh rối loạn sắc tố gồm những bệnh nào và mỗi bệnh có đặc điểm chính gì?"})

    assert reply.status_code == 200
    assert calls
    assert reply.json()["citations"][0]["documentId"] == "pigment"


def test_build_rag_prompt_uses_vietnamese_template():
    prompt = app_module.build_rag_prompt(
        "Ngứa nhiều về đêm là bệnh gì?",
        [
            {
                "documentId": "d1_0002",
                "title": "BỆNH GHẺ - CHẨN ĐOÁN",
                "summary": "Ngứa nhiều, đặc biệt về đêm. Nhiều người trong gia đình có biểu hiện tương tự.",
            }
        ],
    )

    assert "Bạn là trợ lý thông tin da liễu" in prompt
    assert "Ngứa nhiều về đêm là bệnh gì?" in prompt
    assert "BỆNH GHẺ - CHẨN ĐOÁN" in prompt
    assert "Ngứa nhiều, đặc biệt về đêm" in prompt


def test_chat_summarizes_rag_context_with_llm(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    memory_store.clear()
    seen = {}

    async def fake_retrieve(message, image_base64=None):
        return [
            {
                "id": "rag-d1_0002",
                "documentId": "d1_0002",
                "source": "ChromaDB Skin",
                "title": "BỆNH GHẺ - CHẨN ĐOÁN",
                "year": "2026",
                "category": "Chương 2",
                "url": None,
                "summary": "Ngứa nhiều về đêm và có người cùng gia đình bị ngứa là gợi ý quan trọng.",
                "evidenceLevel": "Vector similarity 0.91",
                "metadata": {"vectorSimilarity": 0.91},
            }
        ]

    async def fake_call_llm(prompt):
        seen["prompt"] = prompt
        return "Các dấu hiệu bạn mô tả khá phù hợp với nhóm thông tin về bệnh ghẻ trong tài liệu."

    monkeypatch.setattr(app_module, "retrieve_sources", fake_retrieve)
    monkeypatch.setattr(app_module, "call_llm", fake_call_llm)
    client = TestClient(app)

    reply = client.post("/api/chat", json={"message": "ngứa về đêm, cả nhà cùng ngứa"})

    assert reply.status_code == 200
    payload = reply.json()
    assert payload["text"].startswith("Các dấu hiệu")
    assert "ngứa về đêm, cả nhà cùng ngứa" in seen["prompt"]
    assert "Ngứa nhiều về đêm" in seen["prompt"]


def test_cors_allows_local_frontend_port_3001(monkeypatch):
    monkeypatch.delenv("FRONTEND_ORIGINS", raising=False)
    client = TestClient(app)

    response = client.options(
        "/api/chat",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
