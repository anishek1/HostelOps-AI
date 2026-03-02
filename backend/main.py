"""
main.py — HostelOps AI
=======================
FastAPI application entry point.
Registers all routers, configures CORS, and sets up lifespan events.
Run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the application."""
    # Startup — nothing async required at this stage
    yield
    # Shutdown — clean up resources if needed in future sprints


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HostelOps AI",
    description="Autonomous operations management system for hostels.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — import after app to avoid circular imports
# ---------------------------------------------------------------------------

from routes.auth import router as auth_router        # noqa: E402
from routes.users import router as users_router      # noqa: E402
from routes.complaints import router as complaints_router  # noqa: E402

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(complaints_router, prefix="/api/complaints", tags=["Complaints"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "hostelops-ai"}
