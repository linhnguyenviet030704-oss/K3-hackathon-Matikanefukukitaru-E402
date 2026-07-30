from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user
from .config import cors_origins, supabase_ready
from .guardrails import (
    OFF_TOPIC_RESPONSE,
    build_conversation_context,
    is_dermatology_related,
    latest_citations,
    retrieval_query,
    should_reuse_existing_context,
)
from .rag import build_rag_prompt, call_llm, fallback_rag_answer, retrieve_sources
from .schemas import ChatRequest, ConversationCreate, ConversationPatch, CurrentUser
from .skin_classifier import classify_image_base64
from .storage import (
    add_message,
    add_sources,
    clear_user_conversations,
    conversation_response,
    create_conversation_row,
    delete_conversation_row,
    ensure_owner,
    get_conversation_row,
    list_messages,
    list_source_rows,
    list_visible_conversations,
    memory_store,
    source_response,
    title_from_message,
    update_conversation_row,
)


app = FastAPI(title="DermaCare Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def chat_placeholder(message: str | None, citations: list[dict[str, Any]], conversation_context: str = "") -> str:
    prompt = build_rag_prompt(message, citations, conversation_context)
    text = await call_llm(prompt)
    return text or fallback_rag_answer(message, citations)


def _message_with_classifier(message: str | None, prediction: dict[str, Any] | None) -> str | None:
    if not prediction:
        return message
    hint = _classifier_hint(prediction)
    if not hint:
        return message
    base = (message or "").strip()
    return f"{base}\nSkin-classifier shortlist: {hint}".strip()


def _classifier_hint(prediction: dict[str, Any]) -> str:
    label = prediction.get("pred_class") or ""
    label_vi = prediction.get("pred_class_vi") or ""
    confidence = prediction.get("confidence")
    parts = [part for part in (label_vi, label) if part]
    hint = " / ".join(parts) or "unknown"
    if isinstance(confidence, int | float):
        hint = f"{hint} ({confidence:.0%})"
    return hint


def _show_classifier(text: str, prediction: dict[str, Any] | None) -> str:
    if not prediction:
        return text
    return f"Classifier ảnh: {_classifier_hint(prediction)}\n\n{text}"


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "DermaCare Backend", "storage": "supabase" if supabase_ready() else "memory"}


@app.get("/api/me")
async def me(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": user.id, "authMode": user.auth_mode}


@app.get("/api/conversations")
async def list_conversations(user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = await list_visible_conversations(user)
    return [
        conversation_response(row, await list_messages(row["id"], user), user)
        if user.auth_mode == "supabase"
        else conversation_response(row, user=user)
        for row in rows
    ]


@app.post("/api/conversations")
async def create_conversation(
    payload: ConversationCreate,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    row = await create_conversation_row(payload.title or "New conversation", payload.is_public, user)
    return conversation_response(row, user=user)


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    row = await get_conversation_row(conversation_id, user)
    messages = await list_messages(row["id"], user) if user.auth_mode == "supabase" else None
    return conversation_response(row, messages, user)


@app.patch("/api/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    payload: ConversationPatch,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    existing = await get_conversation_row(conversation_id, user)
    ensure_owner(existing, user)
    values = payload.model_dump(exclude_none=True)
    if "is_public" in values:
        values["is_public"] = bool(values["is_public"])
    row = await update_conversation_row(conversation_id, values, user)
    messages = await list_messages(conversation_id, user) if user.auth_mode == "supabase" else None
    return conversation_response(row, messages, user)


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, bool]:
    existing = await get_conversation_row(conversation_id, user)
    ensure_owner(existing, user)
    await delete_conversation_row(conversation_id, user)
    return {"ok": True}


@app.delete("/api/conversations")
async def clear_conversations(user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    await clear_user_conversations(user)
    return {"ok": True}


@app.get("/api/conversations/{conversation_id}/sources")
async def list_sources(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    return [source_response(source) for source in await list_source_rows(conversation_id, user)]


@app.post("/api/chat")
async def chat(payload: ChatRequest, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    if payload.conversation_id:
        conversation = await get_conversation_row(payload.conversation_id, user)
        ensure_owner(conversation, user)
        conversation_id = payload.conversation_id
    else:
        conversation = await create_conversation_row(title_from_message(payload.message), False, user)
        conversation_id = conversation["id"]

    previous_messages = await list_messages(conversation_id, user) if user.auth_mode == "supabase" else list(conversation.get("messages", []))
    conversation_context = build_conversation_context(previous_messages, payload.history)

    await add_message(
        conversation_id,
        user,
        "user",
        (payload.message or "Analyze attached image").strip(),
        image_base64=payload.image_base64,
        symptom_summary=payload.symptom_summary,
    )

    classifier_prediction = classify_image_base64(payload.image_base64, payload.mime_type) if payload.image_base64 else None
    rag_message = _message_with_classifier(payload.message, classifier_prediction)

    if not is_dermatology_related(payload.message, payload.image_base64, payload.symptom_summary, previous_messages):
        citations = []
        text = OFF_TOPIC_RESPONSE
    elif not classifier_prediction and should_reuse_existing_context(payload.message, previous_messages):
        citations = latest_citations(previous_messages)
        text = await chat_placeholder(payload.message, citations, conversation_context)
    else:
        citations = await retrieve_sources(retrieval_query(rag_message, conversation_context), payload.image_base64)
        text = await chat_placeholder(rag_message, citations, conversation_context)
        text = _show_classifier(text, classifier_prediction)

    assistant_message = await add_message(conversation_id, user, "assistant", text, citations=citations)
    if citations:
        await add_sources(conversation_id, assistant_message["id"], citations, user)

    conversation = await get_conversation_row(conversation_id, user)
    messages = await list_messages(conversation_id, user) if user.auth_mode == "supabase" else None
    return {"text": text, "citations": citations, "conversation": conversation_response(conversation, messages, user)}
