# =============================================================================
# Audio Processing Service
# =============================================================================

from dataclasses import dataclass
from typing import List, Optional
from io import BytesIO
import numpy as np

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AudioValidation:
    """Audio validation result."""
    is_valid: bool
    duration: float
    sample_rate: int
    channels: int
    issues: List[str]


class AudioService:
    """
    Service for audio processing operations.
    
    Handles:
    - Audio format conversion
    - Resampling to 16kHz
    - Mono conversion
    - Quality validation
    """

    async def process_audio(self, audio_data: bytes) -> np.ndarray:
        """
        Process raw audio bytes to numpy array suitable for ASR.
        
        Args:
            audio_data: Raw audio bytes (any supported format)
            
        Returns:
            Numpy array with audio data (16kHz, mono, float32)
        """
        import librosa
        import soundfile as sf

        # Load audio with librosa
        try:
            # Try to load directly
            audio, sr = librosa.load(
                BytesIO(audio_data),
                sr=settings.AUDIO_SAMPLE_RATE,
                mono=True,
            )
        except Exception as e:
            logger.warning("direct_load_failed", error=str(e))
            # Try with pydub for webm/other formats
            audio, sr = await self._convert_with_pydub(audio_data)

        return audio.astype(np.float32)

    async def _convert_with_pydub(self, audio_data: bytes) -> tuple:
        """Convert audio using pydub for format support."""
        from pydub import AudioSegment
        import librosa

        # Load with pydub
        audio_segment = AudioSegment.from_file(BytesIO(audio_data))
        
        # Convert to mono and set sample rate
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(settings.AUDIO_SAMPLE_RATE)
        
        # Export to wav bytes
        wav_buffer = BytesIO()
        audio_segment.export(wav_buffer, format="wav")
        wav_buffer.seek(0)

        # Load with librosa
        audio, sr = librosa.load(wav_buffer, sr=settings.AUDIO_SAMPLE_RATE, mono=True)
        
        return audio, sr

    async def convert(
        self,
        audio_data: bytes,
        target_format: str = "wav",
        sample_rate: int = 16000,
    ) -> bytes:
        """
        Convert audio to target format.
        
        Args:
            audio_data: Source audio bytes
            target_format: Target format (wav, mp3, flac)
            sample_rate: Target sample rate
            
        Returns:
            Converted audio bytes
        """
        from pydub import AudioSegment

        # Load audio
        audio = AudioSegment.from_file(BytesIO(audio_data))
        
        # Set sample rate and mono
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(1)

        # Export to target format
        output = BytesIO()
        audio.export(output, format=target_format)
        output.seek(0)

        return output.read()

    async def validate(self, audio_data: bytes) -> AudioValidation:
        """
        Validate audio for pronunciation analysis.
        
        Checks:
        - Duration (max 30 seconds)
        - Quality (sample rate, channels)
        - Format validity
        """
        from pydub import AudioSegment

        issues: List[str] = []

        try:
            audio = AudioSegment.from_file(BytesIO(audio_data))
        except Exception as e:
            return AudioValidation(
                is_valid=False,
                duration=0,
                sample_rate=0,
                channels=0,
                issues=["Invalid audio format"],
            )

        duration = len(audio) / 1000  # milliseconds to seconds
        sample_rate = audio.frame_rate
        channels = audio.channels

        # Check duration
        if duration > settings.AUDIO_MAX_DURATION:
            issues.append(f"Audio too long ({duration:.1f}s > {settings.AUDIO_MAX_DURATION}s)")
        
        if duration < 0.5:
            issues.append("Audio too short (< 0.5s)")

        # Check sample rate
        if sample_rate < 8000:
            issues.append(f"Sample rate too low ({sample_rate} < 8000 Hz)")

        return AudioValidation(
            is_valid=len(issues) == 0,
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            issues=issues,
        )
