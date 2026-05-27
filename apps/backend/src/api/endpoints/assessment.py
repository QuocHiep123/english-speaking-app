# =============================================================================
# IELTS Speaking Assessment Endpoint
# =============================================================================

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.database import UserAttempt, get_db

logger = get_logger(__name__)

router = APIRouter()

# Reuse the same audio extension whitelist from the STT endpoint
_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".ogg", ".m4a",
    ".webm", ".aac", ".wma", ".opus",
}


@router.post("/assess_speaking")
async def assess_speaking(
    audio: UploadFile = File(..., description="Audio file to assess"),
    prompt_id: Optional[int] = Form(None, description="ID of the IELTS prompt answered"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Full IELTS Speaking assessment pipeline.

    1. Validate audio upload.
    2. Transcribe via Whisper (STT).
    3. Evaluate transcript via Ollama LLM.
    4. Return combined result.
    """
    # Late imports to avoid circular dependency
    from src.main import llm_service, stt_service

    if stt_service is None:
        raise HTTPException(
            status_code=503,
            detail="STT service is not available. Server may still be starting.",
        )
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM evaluation service is not available.",
        )

    # --- Validate upload ---
    if (
        audio.content_type
        and not audio.content_type.startswith("audio/")
        and audio.content_type != "application/octet-stream"
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type '{audio.content_type}'. Expected an audio file.",
        )
    if audio.filename:
        ext = Path(audio.filename).suffix.lower()
        if ext and ext not in _AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'.",
            )

    # --- STT stage ---
    ext = Path(audio.filename).suffix.lower() if audio.filename else ".wav"
    if ext not in _AUDIO_EXTENSIONS:
        ext = ".wav"

    tmp_path: Optional[str] = None
    try:
        contents = await audio.read()
        file_size = len(contents)
        logger.info("assessment_audio_received", size_bytes=file_size, ext=ext)

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file. Please record again.",
            )

        with tempfile.NamedTemporaryFile(
            suffix=ext, delete=False, dir=tempfile.gettempdir(),
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(contents)
            tmp.flush()
            os.fsync(tmp.fileno())

        raw_transcript = await stt_service.transcribe(tmp_path)
        logger.info("assessment_stt_done", transcript_len=len(raw_transcript))

    except FileNotFoundError as exc:
        logger.error("assessment_file_not_found", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        # Hallucination / no-speech detection from STT service
        logger.warning("assessment_stt_no_speech", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("assessment_stt_error")
        raise HTTPException(status_code=500, detail="Speech recognition failed.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # --- LLM evaluation stage ---
    try:
        evaluation = await llm_service.evaluate_transcript(raw_transcript)
        logger.info("assessment_llm_done", has_error="llm_parse_error" in evaluation)
    except Exception as exc:
        logger.exception("assessment_llm_error")
        raise HTTPException(
            status_code=502,
            detail=f"LLM evaluation failed: {type(exc).__name__}: {exc}",
        )

    # --- Save attempt to database ---
    attempt_id = None
    if prompt_id is not None:
        try:
            lexical = evaluation.get("lexical_score")
            grammar = evaluation.get("grammar_score")
            attempt = UserAttempt(
                prompt_id=prompt_id,
                transcript=raw_transcript,
                lexical_score=int(lexical) if lexical is not None else None,
                grammar_score=int(grammar) if grammar is not None else None,
                feedback=evaluation.get("feedback"),
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)
            attempt_id = attempt.id
            logger.info("assessment_saved", attempt_id=attempt_id, prompt_id=prompt_id)
        except Exception as exc:
            db.rollback()
            logger.warning("assessment_save_failed", error=str(exc))

    return JSONResponse(
        content={
            "raw_transcript": raw_transcript,
            "evaluation": evaluation,
            "attempt_id": attempt_id,
        },
    )
