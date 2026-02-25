# =============================================================================
# Health Check Endpoints
# =============================================================================

from fastapi import APIRouter

from src.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    # Add checks for database, model loading, etc.
    return {
        "status": "ready",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}
