"""Application middlewares: security headers, CORS, and a simple rate limiter.

These are intentionally dependency-free (in-memory) so the site stays a single
small container. For multi-instance deploys, swap the rate limiter for a shared
store (e.g. Redis).
"""
import time
import logging
from collections import defaultdict, deque

from aiohttp import web

from app.settings import ALLOWED_ORIGINS

logger = logging.getLogger("middlewares")

# --- Content Security Policy ---------------------------------------------------
# Allows the resources the site actually uses: Google Fonts, cdnjs (Prism), and
# inline scripts/styles currently embedded in templates. Tighten as inline code
# is removed (see roadmap Phase 2).
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

_SECURITY_HEADERS = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


@web.middleware
async def security_headers_middleware(request: web.Request, handler):
    """Attach security headers and minimal CORS to every response."""
    try:
        response = await handler(request)
    except web.HTTPException as exc:
        response = exc

    for key, value in _SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)

    origin = request.headers.get("Origin")
    if origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    if isinstance(response, web.HTTPException):
        raise response
    return response


def rate_limit_middleware(max_requests: int = 5, window_seconds: int = 600):
    """Factory for an in-memory per-IP rate limiter applied to POST requests."""
    hits: dict[str, deque] = defaultdict(deque)

    def _client_ip(request: web.Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote or "unknown"

    @web.middleware
    async def middleware(request: web.Request, handler):
        if request.method == "POST":
            ip = _client_ip(request)
            now = time.monotonic()
            bucket = hits[ip]
            while bucket and now - bucket[0] > window_seconds:
                bucket.popleft()
            if len(bucket) >= max_requests:
                logger.warning("Rate limit exceeded for %s", ip)
                raise web.HTTPTooManyRequests(
                    text="Too many requests. Please try again later."
                )
            bucket.append(now)
        return await handler(request)

    return middleware
