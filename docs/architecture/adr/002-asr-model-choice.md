# ADR-002: Choice of ASR Model

## Status
**Accepted**

## Context
We need to select an Automatic Speech Recognition (ASR) model for transcribing user speech in the pronunciation assessment pipeline.

## Decision Drivers
- Accuracy on English speech from Vietnamese speakers
- Latency requirements (< 500ms for good UX)
- Resource constraints (development on consumer hardware)
- Word-level timestamp support

## Considered Options

### Option 1: OpenAI Whisper (via faster-whisper)
- State-of-the-art accuracy
- Multiple model sizes
- Word-level timestamps
- CTranslate2 optimized

### Option 2: Google Speech-to-Text API
- Cloud-based, no GPU needed
- Pay-per-use pricing
- High accuracy

### Option 3: Wav2Vec2 + LM
- Open-source
- Customizable
- Requires fine-tuning

### Option 4: Azure Speech Services
- Enterprise features
- Pronunciation assessment built-in
- Higher cost

## Decision
**OpenAI Whisper via faster-whisper**

## Rationale
1. **Accuracy**: Best-in-class WER on diverse accents
2. **Self-hosted**: No API costs, data privacy
3. **Timestamps**: Word-level alignment for scoring
4. **Optimization**: faster-whisper uses CTranslate2 (4x faster)
5. **Model flexibility**: Can scale from tiny (39M) to large (1.5B)

## Implementation Details
```python
from faster_whisper import WhisperModel

# Development: "base" model (74M params, ~1GB VRAM)
# Production: "small" or "medium" with GPU

model = WhisperModel("base", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio, word_timestamps=True)
```

## Consequences

### Positive
- High accuracy without API costs
- Privacy-friendly (on-premise)
- Flexible model scaling

### Negative
- Requires GPU for real-time inference
- Model download on first use
- Higher memory usage than API calls

## Metrics to Monitor
- Word Error Rate (WER) on Vietnamese L1 speakers
- Inference latency (P50, P99)
- Memory usage

## Related
- ADR-004 for phoneme alignment approach
- faster-whisper documentation
