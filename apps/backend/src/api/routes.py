# =============================================================================
# API Routes
# =============================================================================

from fastapi import APIRouter

from src.api.endpoints import pronunciation, health, audio

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(pronunciation.router, prefix="/pronunciation", tags=["Pronunciation"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
