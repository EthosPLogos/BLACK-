from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import BLACK_API_KEY

# Paths that bypass the key check entirely
_OPEN_PATHS = {b"/api/health"}


class APIKeyMiddleware:
    """
    Pure ASGI middleware — does not buffer streaming responses (safe for SSE).
    When BLACK_API_KEY is empty the check is skipped entirely (dev mode).
    All requests must include header:  X-BLACK-API-KEY: <key>
    Browser preflight OPTIONS requests are always passed through so CORS works.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Auth disabled — pass everything
        if not BLACK_API_KEY:
            await self.app(scope, receive, send)
            return

        # CORS preflight — must pass through so browser gets CORS headers before auth
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Open paths
        path = scope.get("path", "").encode()
        if path in _OPEN_PATHS:
            await self.app(scope, receive, send)
            return

        # Extract key from headers (ASGI headers are lowercase bytes)
        headers = dict(scope.get("headers", []))
        provided = headers.get(b"x-black-api-key", b"").decode()

        if provided != BLACK_API_KEY:
            response = JSONResponse({"detail": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
