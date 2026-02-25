# =============================================================================
# Backend Unit Tests - API Endpoints
# =============================================================================
"""
Unit tests for API endpoints.

Uses FastAPI TestClient for HTTP-level testing.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import base64
import json

import sys
sys.path.insert(0, "apps/backend")


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/api/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/api/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestPronunciationEndpoints:
    """Tests for pronunciation API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        return TestClient(app)
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a mock audio file."""
        # Create minimal WAV header + silence
        return b"RIFF" + b"\x00" * 100
    
    def test_analyze_requires_audio(self, client):
        """Test that analyze endpoint requires audio file."""
        response = client.post(
            "/api/pronunciation/analyze",
            data={"reference_text": "hello"},
        )
        
        # Should fail without audio
        assert response.status_code == 422
    
    def test_analyze_requires_reference_text(self, client, sample_audio_file):
        """Test that analyze endpoint requires reference text."""
        response = client.post(
            "/api/pronunciation/analyze",
            files={"audio": ("test.wav", sample_audio_file, "audio/wav")},
        )
        
        # Should fail without reference_text
        assert response.status_code == 422
    
    @pytest.mark.skip(reason="Requires mock services")
    def test_analyze_success(self, client, sample_audio_file):
        """Test successful pronunciation analysis."""
        with patch("src.services.pronunciation.PronunciationService.analyze") as mock:
            mock.return_value = MagicMock(
                transcription="hello",
                score=MagicMock(overall=85, accuracy=82, fluency=88, completeness=90),
                feedback=MagicMock(phonemes=[], suggestions=[], vietnamese_interference=None),
            )
            
            response = client.post(
                "/api/pronunciation/analyze",
                files={"audio": ("test.wav", sample_audio_file, "audio/wav")},
                data={"reference_text": "hello"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "score" in data


class TestAudioEndpoints:
    """Tests for audio processing endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        return TestClient(app)
    
    def test_validate_requires_audio(self, client):
        """Test that validate endpoint requires audio file."""
        response = client.post("/api/audio/validate")
        
        assert response.status_code == 422
    
    def test_convert_supported_formats(self, client):
        """Test that convert supports expected formats."""
        # This would test format support
        pass
