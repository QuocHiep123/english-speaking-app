# Model Documentation

## Overview

VietSpeak AI uses multiple ML models for speech processing and pronunciation assessment.

## Models

### 1. Whisper ASR

**Purpose**: Speech-to-Text transcription

**Model**: OpenAI Whisper (via faster-whisper)

**Variants**:
| Model | Parameters | VRAM | Relative Speed |
|-------|------------|------|----------------|
| tiny | 39M | ~1GB | ~32x |
| base | 74M | ~1GB | ~16x |
| small | 244M | ~2GB | ~6x |
| medium | 769M | ~5GB | ~2x |
| large | 1550M | ~10GB | 1x |

**Usage**:
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio, language="en")
```

### 2. Pronunciation Scorer (GOP-based)

**Purpose**: Phoneme-level pronunciation scoring

**Architecture**:
- Backbone: Wav2Vec2 (facebook/wav2vec2-base)
- Fine-tuned on: VIVOS + L2-ARCTIC
- Output: Phoneme probabilities + GOP scores

**GOP (Goodness of Pronunciation)**:

$$GOP(p) = \log P(p | O) - \max_{q \neq p} \log P(q | O)$$

Where:
- $p$ = expected phoneme
- $O$ = acoustic observations
- $q$ = alternative phonemes

**Scoring Scale**:
- 90-100: Excellent (native-like)
- 70-89: Good
- 50-69: Fair (needs practice)
- 0-49: Poor (significant errors)

### 3. G2P (Grapheme-to-Phoneme)

**Purpose**: Convert text to phoneme sequences

**Library**: g2p-en

**Example**:
```python
from g2p_en import G2p

g2p = G2p()
phonemes = g2p("hello")  # ['HH', 'AH0', 'L', 'OW1']
```

## Vietnamese Interference Patterns

Common pronunciation errors for Vietnamese learners:

| English Sound | IPA | Vietnamese Interference | Tip |
|---------------|-----|------------------------|-----|
| /θ/ (th) | θ | → /t/ or /s/ | Tongue between teeth |
| /ð/ (the) | ð | → /d/ or /z/ | Voiced tongue between teeth |
| /r/ | ɹ | → /l/ or /ɾ/ | Curl tongue back |
| Final consonants | various | Often dropped | Pronounce clearly |
| /æ/ (cat) | æ | → /e/ or /a/ | Lower jaw more |
| /ɪ/ vs /iː/ | ɪ, iː | Not distinguished | Short vs long |

## Evaluation Metrics

### 1. GOP Correlation
Pearson correlation between predicted and human-annotated GOP scores.

**Target**: ≥ 0.8

### 2. Phoneme Error Rate (PER)
$$PER = \frac{S + D + I}{N}$$

Where S=substitutions, D=deletions, I=insertions, N=reference phonemes.

**Target**: ≤ 15%

### 3. Word Error Rate (WER)
Standard ASR metric for transcription accuracy.

**Target**: ≤ 10% for clear speech

### 4. Latency
- P50: ≤ 50ms per utterance
- P99: ≤ 200ms per utterance

## Training Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   VIVOS     │────▶│  Data Prep  │────▶│  Training   │
│   Dataset   │     │  Script     │     │   Loop      │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Production  │◀────│  Optimize   │◀────│ Evaluation  │
│   Model     │     │ (ONNX/TRT)  │     │   Script    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Model Versioning

Models are versioned using MLflow:

```
models/
├── pronunciation_scorer/
│   ├── v1.0.0/
│   │   ├── config.json
│   │   ├── model.pt
│   │   └── metrics.json
│   └── latest -> v1.0.0/
└── whisper/
    └── base/
```
