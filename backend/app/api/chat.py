"""WhatsApp-style chat endpoint (simulated channel).

The conversation runs on the same deterministic engine as the web flow. This
is explicitly a DEMO simulator — production WhatsApp integration is a future
provider swap (WebNotificationProvider → WhatsAppProvider).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatTurnOut
from app.services.chat_service import handle_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatIn(BaseModel):
    session_id: str | None = None
    text: str


@router.post("", response_model=ChatTurnOut, summary="Send a farmer message to Unnati")
def chat(payload: ChatIn, db: Session = Depends(get_db)) -> ChatTurnOut:
    session_id = payload.session_id or uuid.uuid4().hex[:12]
    try:
        reply = handle_message(db, session_id, payload.text)
    except Exception:  # noqa: BLE001 - never leak internals into the chat
        from app.services.chat_service import bot

        reply = bot(
            "Something went wrong on my side. Please type *start over* and let's "
            "try again. 🙏"
        )
    return ChatTurnOut(session_id=session_id, reply=reply)
