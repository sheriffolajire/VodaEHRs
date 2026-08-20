"""Redis client configuration for distributed rate limiting and caching."""
import os
from typing import Optional

import redis

from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client singleton.
    
    Returns None if Redis is not configured or unavailable.
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    # Try to get Redis URL from environment
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        # Default local Redis
        redis_url = "redis://localhost:6379/0"
    
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        _redis_client.ping()
        return _redis_client
    except redis.ConnectionError:
        # Redis not available, return None to fall back to in-memory
        return None
    except Exception:
        # Any other error, return None
        return None


def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
