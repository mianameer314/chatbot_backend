# app/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage
from app.core.redis import get_redis
from app.services.sentiments import analyze
from app.services.pdf_loader import load_and_index_pdfs as load_pdfs
import json
import os
from fastapi import UploadFile, File
import shutil


router = APIRouter()

CACHE_TTL_SECONDS = 60 * 5  # 5 minutes

def _cache_key(session_id: str) -> str:
    return f"chat_history:{session_id}"


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    r = get_redis()
    key = _cache_key(session_id)

    try:
        cached = r.get(key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

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
            "created_at": m.created_at.isoformat(),
            "sentiment_label": m.sentiment_label,
            "sentiment_score": m.sentiment_score,
            "tone": m.tone,
        }
        for m in messages
    ]

    try:
        r.setex(key, CACHE_TTL_SECONDS, json.dumps(result))
    except Exception:
        pass

    return result


@router.post("/send")
def send_message(payload: dict, db: Session = Depends(get_db)):
    for field in ("session_id", "role", "content"):
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    s_label = None
    s_score = None
    s_tone = None
    if payload["role"] == "user":
        sa = analyze(payload["content"])
        s_label = sa["label"]
        s_score = sa["score"]
        s_tone  = sa["tone"]

    msg = ChatMessage(
        session_id=payload["session_id"],
        role=payload["role"],
        content=payload["content"],
        sentiment_label=s_label,
        sentiment_score=s_score,
        tone=s_tone,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    try:
        r = get_redis()
        r.delete(_cache_key(payload["session_id"]))
    except Exception:
        pass

    return {
        "status": "ok",
        "message_id": msg.id,
        "sentiment_label": s_label,
        "sentiment_score": s_score,
        "tone": s_tone,
    }


@router.post("/clear/{session_id}")
def clear_history(session_id: str, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()

    try:
        r = get_redis()
        r.delete(_cache_key(session_id))
    except Exception:
        pass

    return {"status": "cleared"}


@router.get("/cache/ping")
def cache_ping():
    try:
        r = get_redis()
        ok = r.ping()
        return {"redis": "ok" if ok else "unreachable"}
    except Exception as e:
        return {"redis": f"error: {e.__class__.__name__}"}

UPLOAD_DIR = "knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload_pdf")
def upload_pdf(file: UploadFile = File(...)):
    try:
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return {"status": "ok", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


# -------------------------------
# 🔹 NEW: Reload PDFs endpoint
# -------------------------------
@router.post("/reload/pdfs")
def reload_pdfs():
    try:
        docs = load_pdfs()  # Load all PDFs from knowledge/
        return {"status": "ok", "files_loaded": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF reload failed: {str(e)}")
