import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.approval_routes import router as approval_router
from app.api.forge_routes import router as forge_router
from app.api.update_routes import router as update_router
from app.api.job_apply_routes import router as job_apply_router
from app.api.audit_routes import router as audit_router
from app.api.backup_routes import router as backup_router
from app.api.brief_routes import router as brief_router
from app.api.email_routes import router as email_router
from app.api.integrations_routes import router as integrations_router
from app.api.memory_routes import router as memory_router
from app.api.routes import router as api_router
from app.api.scheduler_routes import router as scheduler_router
from app.api.voice_routes import router as voice_router
from app.config import BACKEND_VERSION, CORS_ORIGINS
from app.middleware.auth import APIKeyMiddleware
from app.scheduler import runner


@asynccontextmanager
async def lifespan(_app: FastAPI):
    runner.start()
    yield
    runner.stop()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limit on /api/chat endpoints — 60 requests per minute."""

    _MAX = 60
    _WINDOW = 60.0

    def __init__(self, app):
        super().__init__(app)
        self._log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/chat"):
            return await call_next(request)
        ip = (request.client.host if request.client else "unknown")
        now = time.monotonic()
        cutoff = now - self._WINDOW
        timestamps = [t for t in self._log[ip] if t > cutoff]
        if len(timestamps) >= self._MAX:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        timestamps.append(now)
        self._log[ip] = timestamps
        return await call_next(request)


app = FastAPI(
    title="Mr.Black Core",
    description="Local-first AI operating system core",
    version=BACKEND_VERSION,
    lifespan=lifespan,
)

# Middleware registration — last registered = outermost = runs first on requests.
# Order: CORS (outermost) → RateLimit → SecurityHeaders → APIKey → Routes
app.add_middleware(APIKeyMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-BLACK-API-KEY", "Accept", "Authorization"],
)

app.include_router(api_router)
app.include_router(audit_router)
app.include_router(approval_router)
app.include_router(memory_router)
app.include_router(scheduler_router)
app.include_router(voice_router)
app.include_router(integrations_router)
app.include_router(brief_router)
app.include_router(email_router)
app.include_router(backup_router)
app.include_router(job_apply_router)
app.include_router(forge_router)
app.include_router(update_router)
