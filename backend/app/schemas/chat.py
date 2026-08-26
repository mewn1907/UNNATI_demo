"""Chat schemas for the WhatsApp-style conversational experience."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    session_id: str = Field(min_length=6, max_length=64)
    text: str = Field(min_length=1, max_length=1000)


class QuickReply(BaseModel):
    label: str
    value: str


class ChatMessageOut(BaseModel):
    role: Literal["bot"]
    text: str
    quick_replies: list[QuickReply] = []
    recommendation_id: str | None = None
    joined: bool = False


class ChatTurnOut(BaseModel):
    session_id: str
    reply: ChatMessageOut
