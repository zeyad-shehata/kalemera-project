import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Lightweight in-memory sliding window rate limiter.
    Protects sensitive endpoints (auth, orders) from brute-force and flooding.
    """
    def __init__(self, app):
        super().__init__(app)
        # Store requests as: { ip: [(timestamp, path), ...] }
        self._requests: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        
        # Endpoint rate limits: (path_prefix, max_requests, window_seconds)
        self._rules = [
            ("/api/auth/login", 20, 60),      # 20 logins per minute
            ("/api/auth/register", 15, 60),   # 15 registrations per minute
            ("/api/orders", 40, 60),          # 40 order creations per minute
        ]

    async def dispatch(self, request: Request, call_next):
        # Exclude OPTIONS and static files
        if request.method == "OPTIONS" or request.url.path.startswith(("/uploads", "/storage", "/docs", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # Check against matching rules
        for prefix, max_reqs, window in self._rules:
            if path.startswith(prefix) and request.method in ("POST", "PUT", "DELETE"):
                # Clean up expired timestamps for this IP
                self._requests[client_ip] = [
                    (t, p) for (t, p) in self._requests[client_ip] if now - t < window
                ]
                
                matching_count = sum(1 for (t, p) in self._requests[client_ip] if p.startswith(prefix))
                if matching_count >= max_reqs:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests. Please slow down and try again later."}
                    )
                
                self._requests[client_ip].append((now, path))
                break

        return await call_next(request)
