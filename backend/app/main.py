from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.approval_routes import router as approval_router
from app.api.audit_routes import router as audit_router
from app.api.memory_routes import router as memory_router
from app.api.routes import router as api_router
from app.config import BACKEND_VERSION, CORS_ORIGINS
from app.middleware.auth import APIKeyMiddleware

app = FastAPI(
    title="BLACK Core",
    description="Local-first AI operating system core",
    version=BACKEND_VERSION,
)

# Middleware registration — last registered = outermost = runs first on requests.
# Order: CORS (outermost) → APIKey → Routes
# This ensures CORS headers are set on all responses, including 401s.
app.add_middleware(APIKeyMiddleware)  # inner — registered first
app.add_middleware(                   # outer — registered last, runs first
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(audit_router)
app.include_router(approval_router)
app.include_router(memory_router)
