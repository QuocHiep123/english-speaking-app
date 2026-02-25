# =============================================================================
# Pronunciation Analysis Service
# =============================================================================

from dataclasses import dataclass
from typing import List, Optional
import numpy as np

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PhonemeResult:
    """Result for individual phoneme analysis."""
    phoneme: str
    score: float
    expected: str
    actual: str
    suggestion: Optional[str] = None


@dataclass
class PronunciationScore:
    """Overall pronunciation scores."""
    overall: float
    accuracy: float
    fluency: float
    completeness: float


@dataclass
class PronunciationFeedback:
    """Detailed feedback for pronunciation."""
    phonemes: List[PhonemeResult]
    suggestions: List[str]
    vietnamese_interference: Optional[List[str]] = None


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    transcription: str
    score: PronunciationScore
    feedback: PronunciationFeedback


class PronunciationService:
    """
    Service for analyzing English pronunciation.
    
    Implements:
    - Speech-to-Text (ASR) using Whisper
    - Goodness of Pronunciation (GOP) scoring
    - Phoneme-level analysis
    - Vietnamese-specific feedback
    """

    def __init__(self):
        self._asr_model = None
        self._pronunciation_model = None
        self._loaded = False

    async def _ensure_models_loaded(self) -> None:
        """Lazy load models on first use."""
        if self._loaded:
            return

        logger.info("loading_pronunciation_models")
        
        # Load Whisper model for ASR
        # In production, use faster-whisper for better performance
        try:
            from faster_whisper import WhisperModel
            self._asr_model = WhisperModel(
                settings.WHISPER_MODEL,
                device="cuda" if settings.USE_GPU else "cpu",
                compute_type="float16" if settings.USE_GPU else "int8",
            )
        except ImportError:
            import whisper
            self._asr_model = whisper.load_model(settings.WHISPER_MODEL)

        self._loaded = True
        logger.info("pronunciation_models_loaded")

    async def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text."""
        await self._ensure_models_loaded()

        segments, _ = self._asr_model.transcribe(
            audio,
            language="en",
            beam_size=5,
        )
        
        transcription = " ".join([s.text for s in segments])
        return transcription.strip()

    async def analyze(
        self,
        audio: np.ndarray,
        reference_text: str,
    ) -> AnalysisResult:
        """
        Analyze pronunciation of audio against reference text.
        
        Args:
            audio: Audio data as numpy array (16kHz, mono)
            reference_text: Expected text that was spoken
            
        Returns:
            AnalysisResult with scores and feedback
        """
        await self._ensure_models_loaded()

        # Transcribe audio
        transcription = await self.transcribe(audio)

        # Calculate scores (placeholder - implement actual GOP scoring)
        score = await self._calculate_scores(audio, reference_text, transcription)
        
        # Generate feedback
        feedback = await self._generate_feedback(
            reference_text=reference_text,
            transcription=transcription,
            score=score,
        )

        return AnalysisResult(
            transcription=transcription,
            score=score,
            feedback=feedback,
        )

    async def _calculate_scores(
        self,
        audio: np.ndarray,
        reference_text: str,
        transcription: str,
    ) -> PronunciationScore:
        """
        Calculate pronunciation scores using GOP algorithm.
        
        TODO: Implement actual GOP scoring with forced alignment
        """
        # Placeholder scoring based on text similarity
        from difflib import SequenceMatcher
        
        similarity = SequenceMatcher(
            None,
            reference_text.lower(),
            transcription.lower(),
        ).ratio()

        # Generate scores (placeholder)
        overall = similarity * 100
        accuracy = overall * 0.95  # Slight variation
        fluency = overall * 0.9
        completeness = similarity * 100

        return PronunciationScore(
            overall=round(overall, 1),
            accuracy=round(accuracy, 1),
            fluency=round(fluency, 1),
            completeness=round(completeness, 1),
        )

    async def _generate_feedback(
        self,
        reference_text: str,
        transcription: str,
        score: PronunciationScore,
    ) -> PronunciationFeedback:
        """Generate detailed feedback including Vietnamese-specific tips."""
        
        phonemes: List[PhonemeResult] = []
        suggestions: List[str] = []
        vietnamese_interference: List[str] = []

        # Vietnamese-specific pronunciation issues
        vietnamese_issues = {
            "th": "Người Việt thường phát âm 'th' như 't'. Hãy đặt lưỡi giữa hai hàm răng.",
            "s": "Âm 's' cuối từ cần rõ ràng, đừng bỏ qua.",
            "ed": "Đuôi '-ed' có 3 cách phát âm: /t/, /d/, /ɪd/",
            "r": "Âm 'r' trong tiếng Anh khác với tiếng Việt. Uốn cong lưỡi về phía sau.",
        }

        if score.overall < 70:
            suggestions.append("Hãy nói chậm hơn và rõ ràng hơn.")
        if score.fluency < 60:
            suggestions.append("Cố gắng nói liền mạch, không ngắt quãng giữa các từ.")

        # Check for common Vietnamese interference
        ref_lower = reference_text.lower()
        if "th" in ref_lower:
            vietnamese_interference.append(vietnamese_issues["th"])

        return PronunciationFeedback(
            phonemes=phonemes,
            suggestions=suggestions,
            vietnamese_interference=vietnamese_interference if vietnamese_interference else None,
        )
