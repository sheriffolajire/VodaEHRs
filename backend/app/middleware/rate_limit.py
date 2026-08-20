"""Rate limiting middleware for API endpoints.

Provides Redis-based distributed rate limiting with in-memory fallback.
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Dict, List, Optional, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.services.exceptions import PermissionError_

logger = get_logger("rate_limit")


class InMemoryRateLimiter:
    """Fallback in-memory rate limiter with sliding window."""
    
    def __init__(self):
        # Store: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self._window_size = 60  # 1 minute window
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old entries
        self._requests[key] = [
            (ts, count) for ts, count in self._requests[key] 
            if ts > window_start
        ]
        
        # Count requests in current window
        total = sum(count for ts, count in self._requests[key])
        
        if total >= max_requests:
            return False
        
        # Record this request
        self._requests[key].append((now, 1))
        return True
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int = 60) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - window_seconds
        
        total = sum(
            count for ts, count in self._requests[key] 
            if ts > window_start
        )
        return max(0, max_requests - total)


class RedisRateLimiter:
    """Redis-based distributed rate limiter with sliding window."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit using Redis."""
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis sorted set for sliding window
        # Remove old entries
        self._redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = self._redis.zcard(key)
        
        if current_count >= max_requests:
            return False
        
        # Add current request
        self._redis.zadd(key, {str(now): now})
        # Set expiry on the key
        self._redis.expire(key, window_seconds)
        
        return True
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int = 60) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries and count
        self._redis.zremrangebyscore(key, 0, window_start)
        current_count = self._redis.zcard(key)
        
        return max(0, max_requests - current_count)


# Global rate limiter instance (initialized on first use)
_rate_limiter: Optional[InMemoryRateLimiter | RedisRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is not None:
        return _rate_limiter
    
    # Try Redis first
    redis_client = get_redis_client()
    if redis_client:
        _rate_limiter = RedisRateLimiter(redis_client)
        logger.info("Using Redis-based rate limiting")
    else:
        # Fall back to in-memory
        _rate_limiter = InMemoryRateLimiter()
        logger.warning("Redis not available, using in-memory rate limiting")
    
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different limits per endpoint.
    
    Rate limits:
    - Login: 5 requests per minute per IP
    - Password reset: 3 requests per minute per IP
    - General API: 1000 requests per minute per IP (increased for development)
    """
    
    # Endpoint-specific limits: (path_pattern, max_requests, window_seconds)
    LIMITS = {
        "/api/v1/auth/login": (5, 60),
        "/api/v1/auth/password-reset": (3, 60),
    }
    DEFAULT_LIMIT = (1000, 60)  # 1000 requests per minute (increased for dev)
    
    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = [
        "/api/v1/users/me",  # User profile endpoint
        "/api/v1/health",     # Health check
    ]
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Get rate limiter instance
        limiter = get_rate_limiter()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Skip rate limiting for excluded paths
        for excluded in self.EXCLUDED_PATHS:
            if path == excluded or path.endswith(excluded):
                return await call_next(request)
        
        # Find applicable limit
        max_requests, window = self.DEFAULT_LIMIT
        for pattern, (limit, win) in self.LIMITS.items():
            if pattern in path:
                max_requests, window = limit, win
                break
        
        # Create rate limit key
        key = f"{client_ip}:{path}"
        
        # Check rate limit
        if not limiter.is_allowed(key, max_requests, window):
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": f"Rate limit exceeded. Try again in {window} seconds.",
                    "errors": []
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(window),
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = limiter.get_remaining(key, max_requests, window)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        
        return response
