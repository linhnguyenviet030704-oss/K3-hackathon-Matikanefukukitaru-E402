from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import HTTPException

from .config import now, supabase_anon_key, supabase_url
from .schemas import CurrentUser


memory_store: dict[str, Any] = {}


def memory_conversations() -> dict[str, dict[str, Any]]:
    return memory_store.setdefault("conversations", {})


def ensure_owner(row: dict[str, Any], user: CurrentUser) -> None:
    if row.get("user_id") != user.id:
        raise HTTPException(status_code=403, detail="Conversation is read-only for this user")


def title_from_message(message: str | None) -> str:
    text = (message or "New conversation").strip()
    return text[:26] + ("..." if len(text) > 26 else "")


def message_response(row: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "timestamp": row.get("created_at") or row.get("timestamp") or now(),
    }
    if row.get("image_url"):
        payload["image"] = {"url": row["image_url"], "name": row.get("image_name")}
    if row.get("symptom_summary"):
        payload["symptomSummary"] = row["symptom_summary"]
    if "citations" in row and row.get("citations") is not None:
        payload["citations"] = row["citations"]
    return payload


def conversation_response(
    row: dict[str, Any],
    messages: list[dict[str, Any]] | None = None,
    user: CurrentUser | None = None,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "isPublic": bool(row.get("is_public", False)),
        "canEdit": user is None or row.get("user_id") == user.id,
        "createdAt": row.get("created_at") or now(),
        "updatedAt": row.get("updated_at") or row.get("created_at") or now(),
        "messages": [message_response(message) for message in (messages or row.get("messages", []))],
    }


def source_response(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "conversationId": row["conversation_id"],
        "messageId": row.get("message_id"),
        "documentId": row.get("document_id"),
        "source": row["source"],
        "title": row["title"],
        "year": row.get("year"),
        "category": row["category"],
        "url": row.get("url"),
        "summary": row["summary"],
        "evidenceLevel": row["evidence_level"],
        "metadata": row.get("metadata") or {},
        "createdAt": row.get("created_at") or now(),
    }


async def supabase_request(
    method: str,
    path: str,
    user: CurrentUser,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
) -> Any:
    if not user.token:
        raise HTTPException(status_code=500, detail="Supabase token missing")

    headers = {
        "apikey": supabase_anon_key() or "",
        "Authorization": f"Bearer {user.token}",
        "Content-Type": "application/json",
    }
    if method in {"POST", "PATCH", "DELETE"}:
        headers["Prefer"] = "return=representation"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.request(
            method,
            f"{supabase_url()}/rest/v1/{path}",
            headers=headers,
            params=params,
            json=json,
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json() if response.content else []


async def list_messages(conversation_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    return await supabase_request(
        "GET",
        "messages",
        user,
        params={"select": "*", "conversation_id": f"eq.{conversation_id}", "order": "created_at.asc"},
    )


async def create_conversation_row(title: str, is_public: bool, user: CurrentUser) -> dict[str, Any]:
    if user.auth_mode == "supabase":
        rows = await supabase_request(
            "POST",
            "conversations",
            user,
            json={"user_id": user.id, "title": title, "is_public": is_public},
        )
        return rows[0]

    row = {
        "id": str(uuid4()),
        "user_id": user.id,
        "title": title,
        "is_public": is_public,
        "created_at": now(),
        "updated_at": now(),
        "messages": [],
        "sources": [],
    }
    memory_conversations()[row["id"]] = row
    return row


async def get_conversation_row(conversation_id: str, user: CurrentUser) -> dict[str, Any]:
    if user.auth_mode == "supabase":
        rows = await supabase_request(
            "GET",
            "conversations",
            user,
            params={"select": "*", "id": f"eq.{conversation_id}", "limit": "1"},
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Conversation not found")
        row = rows[0]
        if row["user_id"] != user.id and not row.get("is_public"):
            raise HTTPException(status_code=404, detail="Conversation not found")
        return row

    row = memory_conversations().get(conversation_id)
    if not row or (row["user_id"] != user.id and not row.get("is_public")):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return row


async def add_message(
    conversation_id: str,
    user: CurrentUser,
    role: Literal["user", "assistant"],
    content: str,
    *,
    image_base64: str | None = None,
    image_name: str | None = None,
    symptom_summary: dict[str, Any] | None = None,
    citations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row = {
        "conversation_id": conversation_id,
        "user_id": user.id,
        "role": role,
        "content": content,
        "image_url": image_base64,
        "image_name": image_name,
        "symptom_summary": symptom_summary,
        "citations": citations,
    }

    if user.auth_mode == "supabase":
        rows = await supabase_request("POST", "messages", user, json=row)
        return rows[0]

    stored = {"id": str(uuid4()), "created_at": now(), **row}
    memory_conversations()[conversation_id]["messages"].append(stored)
    memory_conversations()[conversation_id]["updated_at"] = stored["created_at"]
    return stored


async def add_sources(
    conversation_id: str,
    message_id: str,
    citations: list[dict[str, Any]],
    user: CurrentUser,
) -> list[dict[str, Any]]:
    rows = [
        {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "document_id": citation.get("documentId"),
            "source": citation["source"],
            "title": citation["title"],
            "year": citation.get("year"),
            "category": citation["category"],
            "url": citation.get("url"),
            "summary": citation["summary"],
            "evidence_level": citation["evidenceLevel"],
            "metadata": citation.get("metadata") or {},
        }
        for citation in citations
    ]

    if user.auth_mode == "supabase":
        return await supabase_request("POST", "conversation_sources", user, json=rows)

    stored = [{"id": str(uuid4()), "created_at": now(), **row} for row in rows]
    memory_conversations()[conversation_id]["sources"].extend(stored)
    return stored


async def list_visible_conversations(user: CurrentUser) -> list[dict[str, Any]]:
    if user.auth_mode == "supabase":
        return await supabase_request(
            "GET",
            "conversations",
            user,
            params={"select": "*", "or": f"(user_id.eq.{user.id},is_public.eq.true)", "order": "updated_at.desc"},
        )

    rows = [row for row in memory_conversations().values() if row["user_id"] == user.id or row.get("is_public")]
    rows.sort(key=lambda row: row.get("updated_at", ""), reverse=True)
    return rows


async def update_conversation_row(conversation_id: str, values: dict[str, Any], user: CurrentUser) -> dict[str, Any]:
    values["updated_at"] = now()
    if user.auth_mode == "supabase":
        rows = await supabase_request(
            "PATCH",
            "conversations",
            user,
            params={"id": f"eq.{conversation_id}", "user_id": f"eq.{user.id}"},
            json=values,
        )
        return rows[0]

    row = memory_conversations()[conversation_id]
    row.update(values)
    return row


async def delete_conversation_row(conversation_id: str, user: CurrentUser) -> None:
    if user.auth_mode == "supabase":
        await supabase_request(
            "DELETE",
            "conversations",
            user,
            params={"id": f"eq.{conversation_id}", "user_id": f"eq.{user.id}"},
        )
    else:
        del memory_conversations()[conversation_id]


async def clear_user_conversations(user: CurrentUser) -> None:
    if user.auth_mode == "supabase":
        await supabase_request("DELETE", "conversations", user, params={"user_id": f"eq.{user.id}"})
    else:
        for key, row in list(memory_conversations().items()):
            if row["user_id"] == user.id:
                del memory_conversations()[key]


async def list_source_rows(conversation_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    row = await get_conversation_row(conversation_id, user)
    if user.auth_mode == "supabase":
        return await supabase_request(
            "GET",
            "conversation_sources",
            user,
            params={"select": "*", "conversation_id": f"eq.{row['id']}", "order": "created_at.desc"},
        )
    return row.get("sources", [])
