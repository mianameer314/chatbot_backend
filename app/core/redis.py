# app/core/redis.py
import os
import redis
from typing import Optional

# Use REDIS_URL injected via Railway’s environment variables
# Example format: redis://default:password@host:6379
REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

# Lazily create a client to avoid crashing if REDIS_URL isn’t set yet
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        if not REDIS_URL:
            # Return a dummy client-like object to avoid import errors if env missing
            class _NoRedis:
                def get(self, *a, **k): return None
                def setex(self, *a, **k): return None
                def delete(self, *a, **k): return None
                def ping(self): return True
            _redis_client = _NoRedis()
        else:
            _redis_client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=True,  # strings in/out (no bytes)
                health_check_interval=30
            )
    return _redis_client
