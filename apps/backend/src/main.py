# =============================================================================
# VietSpeak AI Backend - Main Application
# =============================================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.routes import api_router
from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.services.llm_service import IELTSEvaluatorService
from src.services.stt import SpeechToTextService

logger = get_logger(__name__)

# Global singletons — initialised during lifespan startup
stt_service: Optional[SpeechToTextService] = None
llm_service: Optional[IELTSEvaluatorService] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    global stt_service, llm_service

    # Startup
    setup_logging()

    # Ensure the active database has its tables and at least the bundled
    # IELTS prompts. Works whether we land on Supabase or the SQLite fallback.
    try:
        from src.seed_data import seed_if_empty

        inserted = seed_if_empty()
        logger.info("db_ready", seeded=inserted)
    except Exception as exc:  # noqa: BLE001 — never block startup on seeding
        logger.warning("db_seed_skipped", error=f"{type(exc).__name__}: {exc}")

    # Lightweight cloud-backed services (no local model weights)
    stt_service = SpeechToTextService(model=settings.GROQ_WHISPER_MODEL)
    llm_service = IELTSEvaluatorService(model=settings.GROQ_LLM_MODEL)

    yield

    # Shutdown — release services
    stt_service = None
    llm_service = None


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered English pronunciation analysis API for Vietnamese learners",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
