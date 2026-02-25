# =============================================================================
# Audio Processing Endpoints
# =============================================================================

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from src.services.audio import AudioService
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

audio_service = AudioService()


@router.post("/convert")
async def convert_audio(
    audio: UploadFile = File(...),
    target_format: str = "wav",
    sample_rate: int = 16000,
):
    """
    Convert audio file to target format.
    
    - **audio**: Source audio file
    - **target_format**: Target format (wav, mp3, flac)
    - **sample_rate**: Target sample rate (default: 16000 for speech)
    """
    try:
        audio_data = await audio.read()
        converted = await audio_service.convert(
            audio_data=audio_data,
            target_format=target_format,
            sample_rate=sample_rate,
        )

        return StreamingResponse(
            BytesIO(converted),
            media_type=f"audio/{target_format}",
            headers={
                "Content-Disposition": f'attachment; filename="converted.{target_format}"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("audio_conversion_error")
        raise HTTPException(status_code=500, detail="Audio conversion failed")


@router.post("/validate")
async def validate_audio(
    audio: UploadFile = File(...),
):
    """
    Validate audio file for pronunciation analysis.
    
    Checks:
    - File format
    - Duration
    - Audio quality
    """
    try:
        audio_data = await audio.read()
        validation = await audio_service.validate(audio_data)

        return {
            "valid": validation.is_valid,
            "duration": validation.duration,
            "sample_rate": validation.sample_rate,
            "channels": validation.channels,
            "issues": validation.issues,
        }
    except Exception as e:
        logger.exception("audio_validation_error")
        raise HTTPException(status_code=500, detail="Audio validation failed")
