# =============================================================================
# Pronunciation Analysis Endpoints
# =============================================================================

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.services.pronunciation import PronunciationService
from src.services.audio import AudioService
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize services
pronunciation_service = PronunciationService()
audio_service = AudioService()


class PhonemeScore(BaseModel):
    """Individual phoneme score."""
    phoneme: str
    score: float
    expected: str
    actual: str
    suggestion: Optional[str] = None


class PronunciationScore(BaseModel):
    """Overall pronunciation score."""
    overall: float
    accuracy: float
    fluency: float
    completeness: float


class PronunciationFeedback(BaseModel):
    """Detailed feedback for pronunciation."""
    phonemes: List[PhonemeScore]
    suggestions: List[str]
    vietnamese_interference: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    """Response model for pronunciation analysis."""
    success: bool
    transcription: str
    score: PronunciationScore
    feedback: PronunciationFeedback


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
):
    """
    Analyze pronunciation from audio file.
    
    - **audio**: Audio file (webm, wav, mp3)
    - **reference_text**: The expected text that was spoken
    
    Returns detailed pronunciation scores and feedback.
    """
    try:
        logger.info(
            "pronunciation_analysis_started",
            reference_text=reference_text,
            content_type=audio.content_type,
        )

        # Process audio
        audio_data = await audio.read()
        processed_audio = await audio_service.process_audio(audio_data)

        # Analyze pronunciation
        result = await pronunciation_service.analyze(
            audio=processed_audio,
            reference_text=reference_text,
        )

        logger.info(
            "pronunciation_analysis_completed",
            overall_score=result.score.overall,
        )

        return AnalysisResponse(
            success=True,
            transcription=result.transcription,
            score=result.score,
            feedback=result.feedback,
        )

    except ValueError as e:
        logger.error("pronunciation_analysis_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("pronunciation_analysis_unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
):
    """
    Transcribe audio to text using ASR.
    
    - **audio**: Audio file (webm, wav, mp3)
    
    Returns the transcribed text.
    """
    try:
        audio_data = await audio.read()
        processed_audio = await audio_service.process_audio(audio_data)
        transcription = await pronunciation_service.transcribe(processed_audio)
        
        return {"transcription": transcription}
    
    except Exception as e:
        logger.exception("transcription_error")
        raise HTTPException(status_code=500, detail="Transcription failed")
