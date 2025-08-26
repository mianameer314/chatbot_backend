# app/models.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float, func
from .database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(200), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    # NEW sentiment fields
    sentiment_label = Column(String(20), nullable=True)   # 'Positive' | 'Negative' | 'Neutral'
    sentiment_score = Column(Float, nullable=True)        # e.g., 0.987
    tone = Column(String(20), nullable=True)              # 'Enthusiastic' | ...
    created_at = Column(TIMESTAMP, server_default=func.now())
