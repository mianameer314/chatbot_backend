# app/core/redis.py
import os
import json
import redis
from typing import Optional

# Use REDIS_URL injected via Railway or fallback to local
REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        if not REDIS_URL:
            # Fallback dummy client
            class _NoRedis:
                def get(self, *a, **k): return None
                def setex(self, *a, **k): return None
                def delete(self, *a, **k): return None
                def rpush(self, *a, **k): return None
                def lrange(self, *a, **k): return []
                def ping(self): return True
            _redis_client = _NoRedis()
        else:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                health_check_interval=30,
            )
    return _redis_client


# -------------------------------
# 🔹 Chat-specific helpers
# -------------------------------
def cache_message(session_id: str, role: str, content: str):
    """Push a chat message into Redis list."""
    r = get_redis()
    key = f"chat:{session_id}"
    msg = {"role": role, "content": content}
    try:
        r.rpush(key, json.dumps(msg))
    except Exception:
        pass


def get_cached_messages(session_id: str):
    """Retrieve all chat messages for a session."""
    r = get_redis()
    key = f"chat:{session_id}"
    try:
        data = r.lrange(key, 0, -1)
        return [json.loads(m) for m in data]
    except Exception:
        return []


def clear_cache(session_id: str):
    """Clear chat history for a session."""
    r = get_redis()
    key = f"chat:{session_id}"
    try:
        r.delete(key)
    except Exception:
        pass
