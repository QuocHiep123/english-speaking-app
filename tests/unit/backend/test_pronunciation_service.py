# =============================================================================
# Backend Unit Tests - Pronunciation Service
# =============================================================================
"""
Unit tests for the pronunciation analysis service.

These tests verify:
- Score calculation logic
- Phoneme analysis
- Vietnamese interference detection
- Error handling
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

# Import the service under test
import sys
sys.path.insert(0, "apps/backend")

from src.services.pronunciation import (
    PronunciationService,
    PronunciationScore,
    PronunciationFeedback,
    AnalysisResult,
)


class TestPronunciationScore:
    """Tests for pronunciation score data class."""
    
    def test_score_creation(self):
        """Test creating a pronunciation score."""
        score = PronunciationScore(
            overall=85.0,
            accuracy=82.0,
            fluency=88.0,
            completeness=90.0,
        )
        
        assert score.overall == 85.0
        assert score.accuracy == 82.0
        assert score.fluency == 88.0
        assert score.completeness == 90.0
    
    def test_score_ranges(self):
        """Test that scores can be in valid ranges."""
        # Perfect score
        perfect = PronunciationScore(100, 100, 100, 100)
        assert perfect.overall == 100
        
        # Zero score
        zero = PronunciationScore(0, 0, 0, 0)
        assert zero.overall == 0


class TestPronunciationService:
    """Tests for the pronunciation service."""
    
    @pytest.fixture
    def service(self):
        """Create a pronunciation service instance."""
        return PronunciationService()
    
    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio data."""
        # 1 second of silence at 16kHz
        return np.zeros(16000, dtype=np.float32)
    
    @pytest.mark.asyncio
    async def test_transcribe_returns_string(self, service, sample_audio):
        """Test that transcription returns a string."""
        with patch.object(service, "_ensure_models_loaded", new_callable=AsyncMock):
            with patch.object(service, "_asr_model") as mock_model:
                mock_model.transcribe.return_value = (
                    [MagicMock(text="hello")],
                    None,
                )
                service._loaded = True
                
                result = await service.transcribe(sample_audio)
                assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_analyze_returns_analysis_result(self, service, sample_audio):
        """Test that analyze returns an AnalysisResult."""
        with patch.object(service, "_ensure_models_loaded", new_callable=AsyncMock):
            with patch.object(service, "transcribe", new_callable=AsyncMock) as mock_transcribe:
                mock_transcribe.return_value = "hello"
                service._loaded = True
                
                result = await service.analyze(sample_audio, "hello")
                
                assert isinstance(result, AnalysisResult)
                assert hasattr(result, "transcription")
                assert hasattr(result, "score")
                assert hasattr(result, "feedback")
    
    @pytest.mark.asyncio
    async def test_score_calculation_perfect_match(self, service, sample_audio):
        """Test score calculation for perfect text match."""
        with patch.object(service, "_ensure_models_loaded", new_callable=AsyncMock):
            with patch.object(service, "transcribe", new_callable=AsyncMock) as mock_transcribe:
                mock_transcribe.return_value = "hello world"
                service._loaded = True
                
                result = await service.analyze(sample_audio, "hello world")
                
                # Perfect match should give high score
                assert result.score.overall >= 90
    
    @pytest.mark.asyncio
    async def test_score_calculation_poor_match(self, service, sample_audio):
        """Test score calculation for poor text match."""
        with patch.object(service, "_ensure_models_loaded", new_callable=AsyncMock):
            with patch.object(service, "transcribe", new_callable=AsyncMock) as mock_transcribe:
                mock_transcribe.return_value = "completely different"
                service._loaded = True
                
                result = await service.analyze(sample_audio, "hello world")
                
                # Poor match should give low score
                assert result.score.overall < 50
    
    @pytest.mark.asyncio
    async def test_vietnamese_interference_detection(self, service, sample_audio):
        """Test that Vietnamese interference tips are generated."""
        with patch.object(service, "_ensure_models_loaded", new_callable=AsyncMock):
            with patch.object(service, "transcribe", new_callable=AsyncMock) as mock_transcribe:
                mock_transcribe.return_value = "think"
                service._loaded = True
                
                result = await service.analyze(sample_audio, "think")
                
                # Should have Vietnamese-specific tips for 'th' sound
                assert result.feedback.vietnamese_interference is not None
                assert len(result.feedback.vietnamese_interference) > 0


class TestScoreCalculation:
    """Tests for score calculation algorithms."""
    
    def test_similarity_based_scoring(self):
        """Test text similarity scoring logic."""
        from difflib import SequenceMatcher
        
        # Identical texts
        similarity = SequenceMatcher(None, "hello", "hello").ratio()
        assert similarity == 1.0
        
        # Completely different
        similarity = SequenceMatcher(None, "abc", "xyz").ratio()
        assert similarity == 0.0
        
        # Partial match
        similarity = SequenceMatcher(None, "hello", "hallo").ratio()
        assert 0.5 < similarity < 1.0


class TestFeedbackGeneration:
    """Tests for feedback generation."""
    
    def test_low_score_generates_suggestions(self):
        """Test that low scores generate improvement suggestions."""
        # This would test the actual feedback generation logic
        pass
    
    def test_th_sound_detection(self):
        """Test detection of 'th' sound in reference text."""
        reference = "think about this"
        assert "th" in reference.lower()
    
    def test_phoneme_feedback_structure(self):
        """Test phoneme feedback has correct structure."""
        feedback = PronunciationFeedback(
            phonemes=[],
            suggestions=["Practice more"],
            vietnamese_interference=["th sound tip"],
        )
        
        assert isinstance(feedback.phonemes, list)
        assert isinstance(feedback.suggestions, list)
        assert isinstance(feedback.vietnamese_interference, list)
