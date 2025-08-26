from pydantic import BaseModel
from datetime import datetime

class ChatMessageCreate(BaseModel):
    session_id: str
    role: str
    content: str

class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
