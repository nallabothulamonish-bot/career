from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.services.chatbot_engine import get_chatbot_reply

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reply = get_chatbot_reply(payload.message, db, user.id)
    return {"reply": reply}
