# =============================================================================
# Backend Unit Tests - Audio Service
# =============================================================================
"""
Unit tests for the audio processing service.

These tests verify:
- Audio format conversion
- Resampling
- Validation logic
- Error handling
"""

import pytest
import numpy as np
from io import BytesIO
from unittest.mock import MagicMock, patch, AsyncMock

import sys
sys.path.insert(0, "apps/backend")

from src.services.audio import AudioService, AudioValidation


class TestAudioValidation:
    """Tests for audio validation data class."""
    
    def test_valid_audio(self):
        """Test valid audio validation result."""
        validation = AudioValidation(
            is_valid=True,
            duration=5.0,
            sample_rate=16000,
            channels=1,
            issues=[],
        )
        
        assert validation.is_valid is True
        assert validation.duration == 5.0
        assert len(validation.issues) == 0
    
    def test_invalid_audio_with_issues(self):
        """Test invalid audio with multiple issues."""
        validation = AudioValidation(
            is_valid=False,
            duration=60.0,
            sample_rate=4000,
            channels=2,
            issues=[
                "Audio too long",
                "Sample rate too low",
            ],
        )
        
        assert validation.is_valid is False
        assert len(validation.issues) == 2


class TestAudioService:
    """Tests for the audio service."""
    
    @pytest.fixture
    def service(self):
        """Create an audio service instance."""
        return AudioService()
    
    @pytest.fixture
    def sample_wav_bytes(self):
        """Generate sample WAV audio bytes."""
        import wave
        import struct
        
        # Generate 1 second of silence
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        
        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(struct.pack(f"{samples}h", *([0] * samples)))
        
        buffer.seek(0)
        return buffer.read()
    
    @pytest.mark.asyncio
    async def test_process_audio_returns_numpy_array(self, service, sample_wav_bytes):
        """Test that process_audio returns a numpy array."""
        with patch("librosa.load") as mock_load:
            mock_load.return_value = (np.zeros(16000, dtype=np.float32), 16000)
            
            result = await service.process_audio(sample_wav_bytes)
            
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.float32
    
    @pytest.mark.asyncio
    async def test_validate_valid_audio(self, service, sample_wav_bytes):
        """Test validation of valid audio."""
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_audio = MagicMock()
            mock_audio.__len__ = MagicMock(return_value=5000)  # 5 seconds
            mock_audio.frame_rate = 16000
            mock_audio.channels = 1
            mock_segment.return_value = mock_audio
            
            result = await service.validate(sample_wav_bytes)
            
            assert result.is_valid is True
            assert result.duration == 5.0
    
    @pytest.mark.asyncio
    async def test_validate_too_long_audio(self, service, sample_wav_bytes):
        """Test validation rejects too long audio."""
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_audio = MagicMock()
            mock_audio.__len__ = MagicMock(return_value=60000)  # 60 seconds
            mock_audio.frame_rate = 16000
            mock_audio.channels = 1
            mock_segment.return_value = mock_audio
            
            result = await service.validate(sample_wav_bytes)
            
            assert result.is_valid is False
            assert any("too long" in issue.lower() for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_validate_too_short_audio(self, service, sample_wav_bytes):
        """Test validation rejects too short audio."""
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_audio = MagicMock()
            mock_audio.__len__ = MagicMock(return_value=200)  # 0.2 seconds
            mock_audio.frame_rate = 16000
            mock_audio.channels = 1
            mock_segment.return_value = mock_audio
            
            result = await service.validate(sample_wav_bytes)
            
            assert result.is_valid is False
            assert any("too short" in issue.lower() for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_validate_low_sample_rate(self, service, sample_wav_bytes):
        """Test validation warns about low sample rate."""
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_audio = MagicMock()
            mock_audio.__len__ = MagicMock(return_value=5000)
            mock_audio.frame_rate = 4000  # Very low
            mock_audio.channels = 1
            mock_segment.return_value = mock_audio
            
            result = await service.validate(sample_wav_bytes)
            
            assert result.is_valid is False
            assert any("sample rate" in issue.lower() for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_convert_to_wav(self, service, sample_wav_bytes):
        """Test audio conversion to WAV format."""
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_audio = MagicMock()
            mock_audio.set_frame_rate.return_value = mock_audio
            mock_audio.set_channels.return_value = mock_audio
            mock_audio.export = MagicMock()
            mock_segment.return_value = mock_audio
            
            # This tests the flow, actual conversion would need real audio
            result = await service.convert(
                sample_wav_bytes,
                target_format="wav",
                sample_rate=16000,
            )
            
            mock_audio.set_frame_rate.assert_called_with(16000)
            mock_audio.set_channels.assert_called_with(1)
    
    @pytest.mark.asyncio
    async def test_invalid_audio_format(self, service):
        """Test handling of invalid audio format."""
        invalid_data = b"not audio data"
        
        with patch("pydub.AudioSegment.from_file") as mock_segment:
            mock_segment.side_effect = Exception("Invalid audio")
            
            result = await service.validate(invalid_data)
            
            assert result.is_valid is False
            assert "Invalid audio format" in result.issues


class TestAudioProcessing:
    """Tests for audio processing utilities."""
    
    def test_sample_rate_conversion(self):
        """Test sample rate conversion logic."""
        # Original: 44100 Hz, Target: 16000 Hz
        original_samples = 44100  # 1 second at 44.1kHz
        target_rate = 16000
        original_rate = 44100
        
        expected_samples = int(original_samples * target_rate / original_rate)
        assert expected_samples == 16000
    
    def test_stereo_to_mono(self):
        """Test stereo to mono conversion."""
        # Stereo audio (2 channels)
        stereo = np.array([[1, 2, 3], [4, 5, 6]])  # Shape: (2, 3)
        
        # Average channels for mono
        mono = np.mean(stereo, axis=0)
        
        assert mono.shape == (3,)
        np.testing.assert_array_equal(mono, [2.5, 3.5, 4.5])
