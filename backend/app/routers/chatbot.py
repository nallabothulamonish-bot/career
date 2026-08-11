from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.deps import get_optional_current_user
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.chatbot_engine import get_chatbot_reply

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    user_id = user.id if user else None
    return get_chatbot_reply(
        message=payload.message,
        db=db,
        user_id=user_id,
        session_id=payload.session_id
    )
