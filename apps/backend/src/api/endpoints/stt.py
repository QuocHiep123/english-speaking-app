# =============================================================================
# Speech-to-Text Endpoints
# =============================================================================

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Allowed audio MIME type prefixes and file extensions
_AUDIO_MIME_PREFIXES = ("audio/",)
_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".ogg", ".m4a",
    ".webm", ".aac", ".wma", ".opus",
}


def _validate_audio_upload(file: UploadFile) -> None:
    """Raise HTTPException 400 if the upload is not an audio file."""
    # Check MIME type when the client sends one
    if file.content_type and not file.content_type.startswith(_AUDIO_MIME_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type '{file.content_type}'. Expected an audio file.",
        )

    # Also check extension as a safeguard
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext and ext not in _AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Accepted: {', '.join(sorted(_AUDIO_EXTENSIONS))}",
            )


@router.post("/recognize")
async def recognize_speech(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
) -> JSONResponse:
    """Transcribe an uploaded audio file using Whisper.

    - Validates that the upload is an audio file.
    - Saves to a temporary file, runs STT, cleans up, and returns the transcript.
    """
    # Late import to avoid circular dependency at module level
    from src.main import stt_service

    if stt_service is None:
        raise HTTPException(
            status_code=503,
            detail="STT service is not available. Server may still be starting.",
        )

    _validate_audio_upload(audio)

    # Determine a safe extension for the temp file
    ext = Path(audio.filename).suffix.lower() if audio.filename else ".wav"
    if ext not in _AUDIO_EXTENSIONS:
        ext = ".wav"

    tmp_path: Optional[str] = None
    try:
        # Write upload to a temporary file (librosa needs a file path)
        with tempfile.NamedTemporaryFile(
            suffix=ext, delete=False, dir=tempfile.gettempdir(),
        ) as tmp:
            tmp_path = tmp.name
            contents = await audio.read()
            tmp.write(contents)

        transcript = await stt_service.transcribe(tmp_path)

        return JSONResponse(
            content={"transcript": transcript, "status": "success"},
        )

    except FileNotFoundError as exc:
        logger.error("stt_file_not_found", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("stt_recognize_error")
        raise HTTPException(status_code=500, detail="Speech recognition failed.")
    finally:
        # Always clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
