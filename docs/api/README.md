# API Documentation

## Overview

VietSpeak AI provides RESTful APIs for pronunciation analysis and audio processing.

**Base URL**: `http://localhost:8000/api`

**API Version**: v1

## Authentication

Currently, the API is open for development. Production will use JWT authentication.

## Endpoints

### Health Check

#### GET /health
Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Pronunciation Analysis

#### POST /pronunciation/analyze

Analyze pronunciation from audio file.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `audio`: Audio file (WAV, MP3, WebM)
  - `reference_text`: Expected text (string)

**Example**:
```bash
curl -X POST http://localhost:8000/api/pronunciation/analyze \
  -F "audio=@recording.wav" \
  -F "reference_text=Hello, how are you?"
```

**Response**:
```json
{
  "success": true,
  "transcription": "Hello, how are you?",
  "score": {
    "overall": 85,
    "accuracy": 82,
    "fluency": 88,
    "completeness": 90
  },
  "feedback": {
    "phonemes": [
      {
        "phoneme": "HH",
        "score": 90,
        "expected": "HH",
        "actual": "HH"
      }
    ],
    "suggestions": [
      "Good pronunciation overall!"
    ],
    "vietnamese_interference": [
      "Watch the 'th' sound - place tongue between teeth"
    ]
  }
}
```

---

#### POST /pronunciation/transcribe

Transcribe audio to text.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `audio`: Audio file

**Response**:
```json
{
  "transcription": "Hello, how are you?",
  "confidence": 0.95
}
```

---

### Audio Processing

#### POST /audio/validate

Validate audio file for pronunciation analysis.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `audio`: Audio file

**Response**:
```json
{
  "valid": true,
  "duration": 2.5,
  "sample_rate": 16000,
  "channels": 1,
  "issues": []
}
```

---

#### POST /audio/convert

Convert audio to specified format.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `audio`: Audio file
  - `target_format`: "wav" | "mp3" | "flac"
  - `sample_rate`: Target sample rate (default: 16000)

**Response**: Audio file in target format

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 413 | Payload Too Large | Audio file too large |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

- Development: No limits
- Production: 100 requests/minute per IP

## WebSocket API (Future)

Real-time pronunciation feedback will be available via WebSocket at `/ws/pronunciation`.
