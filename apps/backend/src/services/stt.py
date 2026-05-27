# =============================================================================
# Speech-to-Text Service — Groq Cloud Whisper API
# =============================================================================

from pathlib import Path

from groq import AsyncGroq

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class SpeechToTextService:
    """Cloud-based Speech-to-Text service using Groq's Whisper API.

    Sends audio files to Groq's ``whisper-large-v3`` endpoint and returns
    the transcription text.  No local model weights are loaded.
    """

    def __init__(self, model: str = "whisper-large-v3") -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model = model
        logger.info("stt_service_init", model=self._model, backend="groq")

    async def transcribe(self, audio_file_path: str) -> str:
        """Send an audio file to the Groq Whisper API and return the transcript.

        Args:
            audio_file_path: Path to a WAV / MP3 / WEBM / etc. file.

        Returns:
            Transcribed text string.

        Raises:
            FileNotFoundError: If *audio_file_path* does not exist.
        """
        path = Path(audio_file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        logger.info("stt_request_start", file=path.name)

        with open(path, "rb") as audio_file:
            transcription = await self._client.audio.transcriptions.create(
                file=(path.name, audio_file),
                model=self._model,
                language="en",
                response_format="verbose_json",
            )

        text = transcription.text.strip() if transcription.text else ""

        # Detect Whisper hallucination on silent / empty audio.
        # These phrases are commonly returned when no real speech is present.
        _HALLUCINATION_PATTERNS = {
            "thank you.",
            "thank you",
            "thanks for watching.",
            "thanks for watching",
            "subscribe",
            "like and subscribe",
            "bye.",
            "bye",
            "you",
            "",
        }
        if text.lower() in _HALLUCINATION_PATTERNS:
            logger.warning(
                "stt_hallucination_detected",
                file=path.name,
                hallucinated_text=text,
            )
            raise ValueError(
                "Không phát hiện giọng nói. Vui lòng nói to và rõ hơn, "
                "sau đó thử lại. (No speech detected — the audio may be "
                "silent or too quiet.)"
            )

        logger.info("stt_transcribed", file=path.name, length=len(text))
        return text
