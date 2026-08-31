"""Small in-memory sliding-window rate limiter (per client IP).

Good enough for a prototype / single-instance deployment. For a multi-instance
production deployment, swap this for a Redis-based limiter.
"""
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from utils.config import RATE_LIMIT_PER_MINUTE

_EXEMPT_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = RATE_LIMIT_PER_MINUTE):
        super().__init__(app)
        self.limit = limit_per_minute
        self._hits: dict[str, deque] = defaultdict(deque)

    def _allow(self, key: str) -> bool:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit:
            return False
        window.append(now)
        return True

    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS" or request.url.path in _EXEMPT_PATHS:
            return await call_next(request)
        key = request.client.host if request.client else "anonymous"
        if not self._allow(key):
            return JSONResponse(
                {"detail": "Rate limit exceeded. Please slow down and try again shortly."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
