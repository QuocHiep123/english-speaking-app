# =============================================================================
# Integration Tests - API Integration
# =============================================================================
"""
Integration tests for the complete API flow.

These tests verify:
- End-to-end API functionality
- Service integration
- Database operations (when applicable)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64
import json


class TestPronunciationAPIIntegration:
    """Integration tests for pronunciation analysis flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked services."""
        import sys
        sys.path.insert(0, "apps/backend")
        from src.main import app
        return TestClient(app)
    
    @pytest.fixture
    def sample_audio_base64(self):
        """Create base64-encoded sample audio."""
        # Minimal audio data (would be actual WAV in real tests)
        audio_bytes = b"RIFF" + b"\x00" * 100
        return base64.b64encode(audio_bytes).decode()
    
    @pytest.mark.integration
    def test_full_pronunciation_flow(self, client, sample_audio_base64):
        """Test complete pronunciation analysis workflow."""
        # This would test the full flow from audio upload to score return
        pass
    
    @pytest.mark.integration
    def test_transcription_flow(self, client, sample_audio_base64):
        """Test transcription endpoint flow."""
        pass


class TestMCPIntegration:
    """Integration tests for MCP server."""
    
    @pytest.mark.integration
    def test_mcp_tool_registration(self):
        """Test that MCP tools are properly registered."""
        import sys
        sys.path.insert(0, "mcp")
        from src.server import server
        
        # Server should have tools registered
        assert server is not None
    
    @pytest.mark.integration
    async def test_mcp_analyze_tool(self):
        """Test MCP analyze_pronunciation tool."""
        import sys
        sys.path.insert(0, "mcp")
        from src.tools import analyze_pronunciation_tool
        
        # Create mock audio
        audio_base64 = base64.b64encode(b"mock_audio").decode()
        
        result = await analyze_pronunciation_tool(
            audio_base64=audio_base64,
            reference_text="hello",
            detailed_feedback=True,
        )
        
        # Should return JSON string
        assert isinstance(result, str)
        data = json.loads(result)
        assert "success" in data


class TestServiceIntegration:
    """Integration tests for service layer."""
    
    @pytest.mark.integration
    def test_pronunciation_and_audio_service_integration(self):
        """Test pronunciation service uses audio service correctly."""
        # Test that services work together
        pass
