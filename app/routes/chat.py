# app/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage
from app.core.redis import get_redis
import json

router = APIRouter()

CACHE_TTL_SECONDS = 60 * 5  # 5 minutes

def _cache_key(session_id: str) -> str:
    return f"chat_history:{session_id}"

@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    r = get_redis()
    key = _cache_key(session_id)

    # Try Redis first
    try:
        cached = r.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        # If Redis is down, just fall back to DB
        pass

    # Fallback: DB
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    result = [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]

    # Save in Redis
    try:
        r.setex(key, CACHE_TTL_SECONDS, json.dumps(result))
    except Exception:
        pass

    return result


@router.post("/send")
def send_message(payload: dict, db: Session = Depends(get_db)):
    # Basic validation
    for field in ("session_id", "role", "content"):
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    msg = ChatMessage(
        session_id=payload["session_id"],
        role=payload["role"],
        content=payload["content"],
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Invalidate cache for this session
    try:
        r = get_redis()
        r.delete(_cache_key(payload["session_id"]))
    except Exception:
        pass

    return {"status": "ok", "message_id": msg.id}


@router.post("/clear/{session_id}")
def clear_history(session_id: str, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()

    # Clear Redis cache too
    try:
        r = get_redis()
        r.delete(_cache_key(session_id))
    except Exception:
        pass

    return {"status": "cleared"}


@router.get("/cache/ping")
def cache_ping():
    """Quick health check to see if Redis is reachable."""
    try:
        r = get_redis()
        ok = r.ping()
        return {"redis": "ok" if ok else "unreachable"}
    except Exception as e:
        return {"redis": f"error: {e.__class__.__name__}"}
