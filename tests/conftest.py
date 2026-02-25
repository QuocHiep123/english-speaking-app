# =============================================================================
# Shared Test Fixtures
# =============================================================================
"""
Common test fixtures and utilities.
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Generator
import json


@pytest.fixture
def sample_audio_16k() -> np.ndarray:
    """Generate 1 second of sample audio at 16kHz."""
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Generate a simple sine wave (440 Hz)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    return audio


@pytest.fixture
def sample_audio_bytes() -> bytes:
    """Generate sample WAV bytes."""
    import wave
    import struct
    from io import BytesIO
    
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    
    # Generate silence
    audio_data = [0] * samples
    
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"{samples}h", *audio_data))
    
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_transcription() -> dict:
    """Sample transcription data."""
    return {
        "text": "Hello, how are you?",
        "confidence": 0.95,
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "how", "start": 0.6, "end": 0.8},
            {"word": "are", "start": 0.9, "end": 1.0},
            {"word": "you", "start": 1.1, "end": 1.3},
        ],
    }


@pytest.fixture
def sample_pronunciation_score() -> dict:
    """Sample pronunciation score."""
    return {
        "overall": 85,
        "accuracy": 82,
        "fluency": 88,
        "completeness": 90,
    }


@pytest.fixture
def sample_phoneme_feedback() -> list:
    """Sample phoneme-level feedback."""
    return [
        {"phoneme": "HH", "score": 90, "expected": "HH", "actual": "HH"},
        {"phoneme": "AH", "score": 85, "expected": "AH", "actual": "AH"},
        {"phoneme": "L", "score": 88, "expected": "L", "actual": "L"},
        {"phoneme": "OW", "score": 75, "expected": "OW", "actual": "AO"},
    ]


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    """Create temporary model directory."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    
    # Create mock model config
    config = {
        "model_type": "pronunciation_scorer",
        "version": "0.1.0",
        "backbone": "wav2vec2-base",
    }
    
    with open(model_dir / "config.json", "w") as f:
        json.dump(config, f)
    
    return model_dir


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory with sample manifest."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create sample manifest
    manifest = [
        {
            "audio_path": "sample_001.wav",
            "text": "Hello world",
            "speaker_id": "spk001",
            "duration": 1.5,
        },
        {
            "audio_path": "sample_002.wav",
            "text": "How are you",
            "speaker_id": "spk001",
            "duration": 1.2,
        },
    ]
    
    with open(data_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)
    
    return data_dir


# Vietnamese-specific test fixtures
@pytest.fixture
def vietnamese_interference_samples() -> list:
    """Common Vietnamese interference patterns for testing."""
    return [
        {
            "reference": "think",
            "typical_errors": ["tink", "sink"],
            "phoneme_issue": "θ → t/s",
        },
        {
            "reference": "three",
            "typical_errors": ["tree", "sree"],
            "phoneme_issue": "θr → tr/sr",
        },
        {
            "reference": "red",
            "typical_errors": ["led", "wed"],
            "phoneme_issue": "r → l/w",
        },
        {
            "reference": "cat",
            "typical_errors": ["ca", "cah"],
            "phoneme_issue": "final -t dropped",
        },
    ]
