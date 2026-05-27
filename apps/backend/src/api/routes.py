# =============================================================================
# API Routes
# =============================================================================

from fastapi import APIRouter

from src.api.endpoints import assessment, audio, health, pronunciation, prompts, stt

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(pronunciation.router, prefix="/pronunciation", tags=["Pronunciation"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
api_router.include_router(stt.router, prefix="/v1", tags=["Speech-to-Text"])
api_router.include_router(assessment.router, prefix="/v1", tags=["IELTS Assessment"])
api_router.include_router(prompts.router, prefix="/v1", tags=["IELTS Prompts"])
