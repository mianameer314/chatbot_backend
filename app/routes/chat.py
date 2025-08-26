from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/history/{session_id}", response_model=list[schemas.ChatMessageOut])
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    return messages


@router.post("/send", response_model=schemas.ChatMessageOut)
def send_message(message: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    new_msg = models.ChatMessage(
        session_id=message.session_id,
        role=message.role,
        content=message.content,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg
