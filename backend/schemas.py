from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ConversationCreate(CamelModel):
    title: str | None = None
    is_public: bool = Field(False, alias="isPublic")


class ConversationPatch(CamelModel):
    title: str | None = None
    is_public: bool | None = Field(None, alias="isPublic")


class ChatRequest(CamelModel):
    conversation_id: str | None = Field(None, alias="conversationId")
    message: str | None = None
    image_base64: str | None = Field(None, alias="imageBase64")
    mime_type: str | None = Field(None, alias="mimeType")
    symptom_summary: dict[str, Any] | None = Field(None, alias="symptomSummary")
    history: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class CurrentUser:
    id: str
    token: str | None
    auth_mode: Literal["supabase", "dev"]
