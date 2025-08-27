from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageCreate(BaseModel):
    session_id: str
    role: str
    content: str

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    sentiment_label: Optional[str] = None
    tone: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime

    class Config:
        orm_mode = True
