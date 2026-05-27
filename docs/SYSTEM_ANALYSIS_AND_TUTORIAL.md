# 📖 VietSpeak AI - Phân Tích Hệ Thống & Hướng Dẫn Toàn Diện

> Tài liệu này giải thích chi tiết toàn bộ hệ thống VietSpeak AI mà bạn đã xây dựng, đánh giá những gì còn thiếu, và hướng dẫn bạn hiểu từng phần code.

---

## 📋 Mục Lục

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc Chi Tiết](#2-kiến-trúc-chi-tiết)
3. [Frontend (Next.js)](#3-frontend-nextjs)
4. [Backend (FastAPI)](#4-backend-fastapi)
5. [AI Core (ML Pipeline)](#5-ai-core-ml-pipeline)
6. [MCP Server](#6-mcp-server)
7. [Infrastructure](#7-infrastructure)
8. [Testing](#8-testing)
9. [Đánh Giá: Những Gì Đã Hoàn Thành](#9-đánh-giá-những-gì-đã-hoàn-thành)
10. [Đánh Giá: Những Gì Còn Thiếu](#10-đánh-giá-những-gì-còn-thiếu)
11. [Roadmap Đề Xuất](#11-roadmap-đề-xuất)

---

## 1. Tổng Quan Hệ Thống

### VietSpeak AI là gì?

VietSpeak AI là một ứng dụng luyện phát âm tiếng Anh **chuyên biệt cho người Việt**, sử dụng AI để:

- **Thu âm** giọng nói người dùng qua trình duyệt
- **Nhận dạng giọng nói** (ASR - Automatic Speech Recognition) bằng Whisper
- **Chấm điểm phát âm** (GOP - Goodness of Pronunciation)
- **Phản hồi cụ thể** cho lỗi phổ biến của người Việt (ví dụ: "th" → "t", bỏ phụ âm cuối)

### Kiến trúc tổng quan

```
┌──────────────────────────────────────────────────────────────┐
│                   NGƯỜI DÙNG (User)                           │
│     Nói vào microphone → Nhận điểm số & góp ý               │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Frontend (Next.js)    │  ← Giao diện web
              │   Port 3000            │
              └────────────┬────────────┘
                           │ HTTP API
              ┌────────────▼────────────┐
              │   Backend (FastAPI)     │  ← Xử lý logic
              │   Port 8000            │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   AI Core (PyTorch)     │  ← Mô hình ML
              │   Whisper + Wav2Vec2   │
              └─────────────────────────┘
              
              ┌─────────────────────────┐
              │   MCP Server            │  ← Tích hợp Claude AI
              │   Port 8080            │
              └─────────────────────────┘
```

### Công nghệ sử dụng

| Phần | Công nghệ | Mục đích |
|------|-----------|----------|
| Frontend | Next.js 14, React 18, TailwindCSS | Giao diện web, thu âm |
| Backend | FastAPI, Pydantic, Uvicorn | REST API, xử lý audio |
| AI/ML | PyTorch, Whisper, Wav2Vec2 | Nhận dạng giọng nói, chấm điểm |
| Database | PostgreSQL, Redis | Lưu trữ, cache |
| MCP | MCP SDK, stdio/HTTP | Tích hợp Claude Desktop |
| DevOps | Docker, Nginx, Turborepo | Container hóa, monorepo |
| Testing | Pytest, Jest, Cypress | Unit/Integration/E2E test |
| Tracking | MLflow, W&B | Theo dõi thí nghiệm ML |

---

## 2. Kiến Trúc Chi Tiết

### Monorepo Structure

Dự án sử dụng **Turborepo** để quản lý monorepo - nghĩa là tất cả code (frontend, backend, AI, MCP) nằm trong **1 repository duy nhất**.

```
speaking_app/                  ← Root
├── package.json               ← Turborepo config, workspace definition
├── turbo.json                 ← Task pipeline (build, dev, test, lint)
├── Makefile                   ← Development commands (make dev, make test...)
├── pytest.ini                 ← Python test configuration
│
├── apps/                      ← Ứng dụng chính
│   ├── frontend/              ← Next.js web app
│   └── backend/               ← FastAPI API server
│
├── ai-core/                   ← Machine Learning pipeline
│   ├── scripts/               ← Training, evaluation scripts
│   ├── configs/               ← YAML configurations
│   ├── data/                  ← Datasets (raw + processed)
│   ├── models/                ← Trained model weights
│   └── src/                   ← ML source code
│
├── mcp/                       ← Model Context Protocol server
│   └── src/                   ← MCP tools & server
│
├── tests/                     ← Tất cả tests
│   ├── unit/                  ← Unit tests
│   ├── integration/           ← Integration tests
│   └── e2e/                   ← End-to-end tests (Cypress)
│
├── infra/                     ← Infrastructure
│   └── docker/                ← Dockerfiles, compose, nginx
│
└── docs/                      ← Documentation
    ├── architecture/          ← Kiến trúc + ADR
    ├── api/                   ← API docs
    ├── models/                ← Model docs
    └── setup/                 ← Setup guide
```

### Tại sao Monorepo?

**ADR-001** giải thích quyết định này:
- Team nhỏ (1-3 người) → 1 repo dễ quản lý hơn
- Frontend và Backend chia sẻ types → dễ đồng bộ
- Thay đổi breaking change → 1 PR duy nhất
- Portfolio project → dễ review

---

## 3. Frontend (Next.js)

### Cấu trúc Frontend

```
apps/frontend/
├── src/
│   ├── app/                   ← Next.js App Router
│   │   ├── page.tsx           ← Trang chủ
│   │   ├── layout.tsx         ← Layout chung (font, metadata)
│   │   ├── providers.tsx      ← React Query provider
│   │   └── globals.css        ← Global CSS + TailwindCSS
│   │
│   ├── components/
│   │   └── speaking/          ← Components cho chức năng luyện nói
│   │       ├── SpeakingPractice.tsx  ← Component chính
│   │       ├── RecordButton.tsx      ← Nút ghi âm
│   │       ├── ScoreDisplay.tsx      ← Hiển thị điểm
│   │       └── FeedbackPanel.tsx     ← Panel góp ý chi tiết
│   │
│   ├── hooks/                 ← Custom React hooks
│   │   ├── useAudioRecorder.ts       ← Hook thu âm microphone
│   │   └── usePronunciationScore.ts  ← Hook gọi API chấm điểm
│   │
│   ├── lib/
│   │   └── api.ts             ← Axios client configuration
│   │
│   └── types/
│       └── index.ts           ← TypeScript type definitions
│
├── package.json               ← Dependencies
├── next.config.js             ← Next.js config + API proxy
├── tailwind.config.js         ← TailwindCSS config
└── tsconfig.json              ← TypeScript config
```

### Giải thích từng file quan trọng

#### `page.tsx` - Trang chủ
```tsx
// Đây là trang chính. Nó import component SpeakingPractice và hiển thị.
// Next.js 14 App Router: mỗi file page.tsx trong app/ tự động thành 1 route.
export default function Home() {
  return (
    <main>
      <header>VietSpeak AI</header>
      <SpeakingPractice />   {/* Component luyện nói chính */}
    </main>
  );
}
```

#### `useAudioRecorder.ts` - Hook thu âm
```typescript
// Hook này dùng Web API MediaRecorder để thu âm từ microphone.
// Luồng hoạt động:
// 1. getUserMedia() → xin quyền microphone
// 2. MediaRecorder → thu âm thành chunks
// 3. stopRecording() → gom chunks thành Blob
// 4. Blob được gửi lên Backend để phân tích

// Cấu hình audio:
// - sampleRate: 16000 Hz (chuẩn cho speech processing)
// - channelCount: 1 (mono)
// - echoCancellation: true (loại bỏ echo)
// - noiseSuppression: true (giảm nhiễu)
// - Format: WebM/Opus (codec hiệu quả cho web)
```

#### `usePronunciationScore.ts` - Hook gọi API
```typescript
// Hook này gọi Backend API để phân tích phát âm.
// Luồng:
// 1. Nhận audioBlob (từ useAudioRecorder) + referenceText
// 2. Tạo FormData (multipart/form-data để gửi file audio)
// 3. POST /api/pronunciation/analyze
// 4. Nhận về: score (điểm) + feedback (góp ý)
// 5. Cập nhật state → UI tự re-render
```

#### `SpeakingPractice.tsx` - Component chính
```typescript
// Đây là "bộ não" của frontend. Nó:
// 1. Hiển thị câu mẫu (SAMPLE_PHRASES) để user đọc
// 2. Nút ghi âm: bấm 1 lần → startRecording, bấm lần 2 → stopRecording
// 3. Khi stop → gửi audio lên API → nhận điểm
// 4. Hiển thị ScoreDisplay và FeedbackPanel

// State flow:
// isRecording → RecordButton hiển thị animation
// score → ScoreDisplay hiển thị điểm 4 mục
// feedback → FeedbackPanel hiển thị góp ý chi tiết
```

#### `api.ts` - Axios Client
```typescript
// Cấu hình Axios:
// - baseURL: "/api" → proxy qua Next.js rewrites → http://localhost:8000/api
// - timeout: 30s (phân tích audio có thể mất thời gian)
// - Interceptors: tự đính JWT token & xử lý 401 Unauthorized
```

### Data Flow (Frontend)

```
User bấm Record → useAudioRecorder.startRecording()
                 → MediaRecorder bắt đầu thu
                 
User bấm Stop   → useAudioRecorder.stopRecording()
                 → Trả về Blob
                 
                 → usePronunciationScore.analyzeAudio(blob, text)
                 → POST /api/pronunciation/analyze (FormData)
                 → Backend xử lý...
                 → Nhận JSON response
                 
                 → setScore() → ScoreDisplay render
                 → setFeedback() → FeedbackPanel render
```

---

## 4. Backend (FastAPI)

### Cấu trúc Backend

```
apps/backend/
├── src/
│   ├── main.py                ← Entry point, FastAPI app
│   ├── api/
│   │   ├── routes.py          ← Router aggregation
│   │   └── endpoints/
│   │       ├── pronunciation.py  ← /pronunciation/analyze, /transcribe
│   │       ├── audio.py          ← /audio/convert, /validate
│   │       └── health.py         ← /health, /health/ready, /health/live
│   │
│   ├── core/
│   │   ├── config.py          ← Settings (pydantic-settings)
│   │   └── logging.py         ← Structured logging (structlog)
│   │
│   └── services/
│       ├── pronunciation.py   ← Pronunciation analysis logic
│       └── audio.py           ← Audio processing logic
│
├── requirements.txt           ← Production dependencies
├── requirements-dev.txt       ← Development dependencies
└── pyproject.toml             ← Python project config + tool settings
```

### Giải thích từng phần

#### `main.py` - Entry Point
```python
# Tạo FastAPI app với:
# 1. Lifespan handler: startup (load models) / shutdown (cleanup)
# 2. CORS middleware: cho phép frontend (localhost:3000) gọi API
# 3. GZip middleware: nén response > 1KB
# 4. Router: mount tất cả routes dưới /api prefix
# 5. Health check: /health endpoint cho Docker HEALTHCHECK
```

#### `config.py` - Cấu hình
```python
# Dùng pydantic-settings để load config từ environment variables.
# Ưu điểm:
# - Type-safe: mỗi setting có type rõ ràng
# - Validation: tự kiểm tra giá trị hợp lệ
# - .env support: đọc từ file .env
# - Cache: @lru_cache → chỉ tạo 1 lần
#
# Các setting quan trọng:
# - WHISPER_MODEL: "base" (có thể đổi thành tiny/small/medium/large)
# - AUDIO_SAMPLE_RATE: 16000 Hz
# - AUDIO_MAX_DURATION: 30 giây
# - USE_GPU: True/False
# - DATABASE_URL: PostgreSQL connection string
# - REDIS_URL: Redis connection string
```

#### `pronunciation.py` (Service) - Logic chấm điểm
```python
# Đây là SERVICE CHÍNH của hệ thống. Nó:
#
# 1. Lazy Loading: Models chỉ được load khi cần (tiết kiệm RAM)
#    - faster-whisper (ưu tiên) hoặc openai-whisper (fallback)
#
# 2. transcribe(): Chuyển audio → text dùng Whisper
#    - Language: "en" (tiếng Anh)
#    - Beam size: 5 (cân bằng tốc độ/chất lượng)
#
# 3. analyze(): Pipeline chính:
#    audio → transcribe → calculate_scores → generate_feedback → result
#
# 4. _calculate_scores(): ⚠️ HIỆN TẠI ĐANG LÀ PLACEHOLDER
#    - Dùng SequenceMatcher so sánh text (chưa phải GOP thực)
#    - Cần implement forced alignment + GOP scoring
#
# 5. _generate_feedback(): Tạo góp ý cho người Việt
#    - Kiểm tra "th" trong text → góp ý âm "th"
#    - Score < 70 → gợi ý nói chậm hơn
#    - Fluency < 60 → gợi ý nói liền mạch
```

#### `audio.py` (Service) - Xử lý audio
```python
# Service xử lý audio:
#
# 1. process_audio(): Chuyển raw bytes → numpy array
#    - Thử librosa.load() trước (hỗ trợ WAV, FLAC, MP3...)
#    - Fallback: dùng pydub (hỗ trợ WebM, OGG...)
#    - Output: float32 numpy array, 16kHz, mono
#
# 2. convert(): Chuyển đổi format audio
#    - Dùng pydub (dựa trên FFmpeg)
#    - Hỗ trợ: wav, mp3, flac
#
# 3. validate(): Kiểm tra audio trước khi phân tích
#    - Duration: 0.5s - 30s
#    - Sample rate: >= 8000 Hz
#    - Format: phải đọc được
```

### API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Health check cơ bản |
| GET | `/api/health/ready` | Readiness check (Kubernetes) |
| GET | `/api/health/live` | Liveness check (Kubernetes) |
| POST | `/api/pronunciation/analyze` | **Chấm điểm phát âm** |
| POST | `/api/pronunciation/transcribe` | Chuyển audio → text |
| POST | `/api/audio/convert` | Chuyển đổi format audio |
| POST | `/api/audio/validate` | Kiểm tra audio hợp lệ |

### API Request/Response Flow

```
POST /api/pronunciation/analyze
├── Input:
│   ├── audio: file (webm/wav/mp3)
│   └── reference_text: string ("Hello, how are you?")
│
├── Processing:
│   ├── AudioService.process_audio(raw_bytes) → numpy array
│   ├── PronunciationService.transcribe(audio) → "Hello how are you"
│   ├── PronunciationService._calculate_scores() → scores
│   └── PronunciationService._generate_feedback() → feedback
│
└── Output:
    {
      "success": true,
      "transcription": "Hello how are you",
      "score": {
        "overall": 85.0,
        "accuracy": 80.75,
        "fluency": 76.5,
        "completeness": 85.0
      },
      "feedback": {
        "phonemes": [],
        "suggestions": ["Hãy nói chậm hơn..."],
        "vietnamese_interference": ["Âm 'th' cần đặt lưỡi..."]
      }
    }
```

---

## 5. AI Core (ML Pipeline)

### Cấu trúc AI Core

```
ai-core/
├── scripts/
│   ├── data_prep.py               ← Chuẩn bị datasets
│   ├── train.py                   ← Training model
│   ├── evaluate.py                ← Đánh giá model
│   └── extract_l2arctic_errors.py ← Extract lỗi phát âm từ L2-ARCTIC
│
├── configs/
│   ├── train_config.yaml          ← Config training
│   └── eval_config.yaml           ← Config evaluation
│
├── data/
│   ├── raw/                       ← Dữ liệu thô
│   │   ├── HQTV/                  ← Vietnamese speaker 1
│   │   ├── PNV/                   ← Vietnamese speaker 2
│   │   ├── THV/                   ← Vietnamese speaker 3
│   │   └── TLV/                   ← Vietnamese speaker 4
│   └── processed/
│       └── vietnamese_errors.csv  ← 4910 lỗi đã extract
│
├── models/                        ← Model weights (chưa có)
├── src/                           ← ML source code (gần trống)
└── requirements.txt               ← ML dependencies
```

### Giải thích các script

#### `extract_l2arctic_errors.py` - Script đã hoạt động! ✅
```python
# Script này ĐÃ CHẠY THÀNH CÔNG. Nó:
# 1. Đọc TextGrid files từ L2-ARCTIC corpus (4 Vietnamese speakers)
# 2. Parse annotation tier "phones" 
# 3. Tìm error patterns:
#    - "DH,D,s" = Substitution: kỳ vọng DH, nói thành D
#    - "R,sil,d" = Deletion: kỳ vọng R, nhưng bị bỏ (im lặng)
#    - "sil,AH0,a" = Addition: thêm AH0 vào chỗ không nên có
# 4. Output: vietnamese_errors.csv với 4910 lỗi
#
# Đây là DATA thực sự có giá trị cho nghiên cứu!
```

#### `data_prep.py` - Chuẩn bị dữ liệu
```python
# Script chuẩn bị datasets cho training:
# 1. Hỗ trợ VIVOS dataset (Vietnamese read speech)
# 2. Chia train/val/test (80/10/10)
# 3. Generate phoneme labels qua G2P
# 4. Output: manifest.json cho mỗi split
#
# ⚠️ Hiện tại chủ yếu là placeholder/sample data
```

#### `train.py` - Training model
```python
# Script training pronunciation scorer:
#
# Model Architecture:
# ┌─────────────────┐
# │   Audio Input    │ (16000 samples = 1 giây)
# └────────┬────────┘
#          ▼
# ┌─────────────────┐
# │    Encoder       │ Linear(16000→1024) → ReLU → Linear(1024→256)
# └────────┬────────┘
#          ├──────────────────┐
#          ▼                  ▼
# ┌─────────────────┐ ┌─────────────────┐
# │ Phoneme Head    │ │   GOP Head      │
# │ Linear(256→44)  │ │ Linear(256→1)   │
# └─────────────────┘ └─────────────────┘
#
# ⚠️ Model hiện tại là PLACEHOLDER - chưa dùng Wav2Vec2 backbone thực
# Config: AdamW optimizer, cosine scheduler, early stopping
```

#### `evaluate.py` - Đánh giá model
```python
# Script đánh giá model:
# 1. Tính GOP correlation (predicted vs ground truth)
# 2. Phoneme accuracy
# 3. Word Error Rate (WER) - implementation thực bằng dynamic programming
# 4. Latency benchmarks (P50, P90, P99)
# 5. Error analysis: Vietnamese-specific patterns
# 6. Output: HTML report + metrics.json
#
# ⚠️ Hiện tại trả về placeholder results
```

### L2-ARCTIC Data Analysis

File `vietnamese_errors.csv` chứa **4910 lỗi** từ 4 người Việt:

| Speaker | Ý nghĩa |
|---------|----------|
| HQTV | Vietnamese speaker - Hồ Quốc T.V |
| PNV | Vietnamese speaker - Phạm N.V |
| THV | Vietnamese speaker - Trần H.V |
| TLV | Vietnamese speaker - Trương L.V |

Ví dụ lỗi phổ biến:
```
DH,D,s  → "the" phát âm thành "de" (substitution)
R,sil,d → Bỏ âm "r" (deletion)  
TH,T,s  → "think" phát âm thành "tink" (substitution)
```

---

## 6. MCP Server

### MCP là gì?

**MCP (Model Context Protocol)** là giao thức cho phép AI assistants (Claude, v.v.) gọi tools bên ngoài. VietSpeak MCP Server cho phép Claude **trực tiếp phân tích phát âm**.

### Cấu trúc

```
mcp/
├── src/
│   ├── server.py    ← MCP server (stdio + HTTP transport)
│   ├── tools.py     ← Tool implementations
│   └── config.py    ← Server configuration
├── claude_desktop_config.json  ← Config cho Claude Desktop
└── requirements.txt
```

### 4 Tools được expose

| Tool | Mô tả |
|------|-------|
| `analyze_pronunciation` | Phân tích phát âm từ audio base64 |
| `transcribe_audio` | Chuyển audio → text |
| `get_phoneme_feedback` | Góp ý phoneme cho người Việt |
| `compare_pronunciation` | So sánh 2 lần thử để theo dõi tiến bộ |

### Luồng hoạt động

```
Claude Desktop ──stdio──► MCP Server
                             │
                             ├── analyze_pronunciation()
                             ├── transcribe_audio()
                             ├── get_phoneme_feedback()
                             └── compare_pronunciation()
                                     │
                                     ▼
                              Backend API (FastAPI)
```

### ⚠️ Lưu ý

Tất cả 4 tools hiện tại **trả về dữ liệu placeholder** (hardcoded). Chưa kết nối thực sự với Backend API.

---

## 7. Infrastructure

### Docker Setup

```
infra/docker/
├── docker-compose.yml       ← Production (frontend*2, backend*2, nginx, db, redis)
├── docker-compose.dev.yml   ← Development (+ mlflow, hot-reload)
├── frontend.Dockerfile      ← Multi-stage build (deps → builder → runner)
├── backend.Dockerfile       ← Multi-stage build (builder → runtime, có FFmpeg)
├── ai-core.Dockerfile       ← NVIDIA CUDA image cho GPU training
└── nginx/
    └── nginx.conf           ← Reverse proxy + rate limiting
```

### Production Architecture (docker-compose.yml)

```
                    ┌──────────┐
                    │  Nginx   │ :80, :443
                    │(reverse  │
                    │ proxy)   │
                    └────┬─────┘
                         │
            ┌────────────┼────────────┐
            ▼                         ▼
    ┌──────────────┐         ┌──────────────┐
    │  Frontend x2 │ :3000   │  Backend x2  │ :8000
    │  (Next.js)   │         │  (FastAPI)   │
    └──────────────┘         └──────┬───────┘
                                    │
                         ┌──────────┼──────────┐
                         ▼                     ▼
                  ┌──────────┐          ┌──────────┐
                  │PostgreSQL│ :5432    │  Redis   │ :6379
                  └──────────┘          └──────────┘
```

### Development Architecture (docker-compose.dev.yml)

Thêm:
- **MCP Server** (port 8080)
- **MLflow** (port 5000) - experiment tracking
- **Hot reload** cho cả frontend và backend
- Volume mounts cho code changes

### Nginx Configuration

```nginx
# Tính năng:
# 1. Reverse proxy: / → frontend, /api → backend
# 2. Rate limiting: 100 requests/phút cho API
# 3. Burst: cho phép 20 requests burst
# 4. Max body size: 50MB (cho audio upload)
# 5. WebSocket support cho frontend hot-reload
```

---

## 8. Testing

### Cấu trúc Test

```
tests/
├── conftest.py                    ← Shared fixtures
├── unit/
│   ├── backend/
│   │   ├── test_api_endpoints.py      ← 7 tests
│   │   ├── test_pronunciation_service.py ← 10 tests
│   │   └── test_audio_service.py      ← 11 tests
│   ├── ai_core/
│   │   └── test_model_evaluation.py   ← ML tests
│   └── frontend/
│       ├── hooks.test.ts              ← Hook tests
│       └── SpeakingPractice.test.tsx  ← Component tests
├── integration/
│   └── test_api_integration.py        ← API flow tests
└── e2e/
    └── cypress/                       ← E2E browser tests
```

### Fixtures đáng chú ý (conftest.py)

```python
# Các fixture dùng chung:
# - sample_audio_16k: 1 giây sine wave 440Hz ở 16kHz
# - sample_audio_bytes: WAV bytes
# - sample_transcription: mock transcription result
# - sample_pronunciation_score: mock score data
# - vietnamese_interference_samples: test cases cho lỗi người Việt
#   Ví dụ: "think" → ["tink", "sink"], "red" → ["led", "wed"]
```

### Test Coverage

| Area | Tests | Status |
|------|-------|--------|
| Health endpoints | 3 | ✅ Hoạt động |
| Pronunciation API | 3 | ⚠️ 1 skipped |
| Audio API | 1 | ⚠️ Placeholder |
| Pronunciation Service | 5 | ✅ Mock-based |
| Audio Service | 8 | ✅ Mock-based |
| Score Calculation | 3 | ✅ Hoạt động |
| MCP Integration | 2 | ⚠️ Placeholder |
| Frontend | 2 | ⚠️ Skeleton |

---

## 9. Đánh Giá: Những Gì Đã Hoàn Thành ✅

### Architecture & Structure (90%)
- ✅ Monorepo structure với Turborepo rõ ràng
- ✅ ADR (Architecture Decision Records) chuyên nghiệp
- ✅ Makefile với đầy đủ commands
- ✅ Docker setup cho cả dev và production
- ✅ Nginx reverse proxy với rate limiting
- ✅ Structured logging (structlog)
- ✅ Config management (pydantic-settings)
- ✅ Multi-stage Docker builds

### Frontend (85%)
- ✅ Next.js 14 App Router
- ✅ Audio recording hook (MediaRecorder API)
- ✅ API client (Axios) với interceptors
- ✅ React Query cho state management
- ✅ Component architecture tốt (SpeakingPractice, RecordButton, ScoreDisplay, FeedbackPanel)
- ✅ TailwindCSS styling
- ✅ TypeScript types
- ✅ Vietnamese UI text

### Backend (75%)
- ✅ FastAPI với async support
- ✅ RESTful API design
- ✅ Audio processing pipeline (librosa + pydub)
- ✅ Audio validation (duration, format, sample rate)
- ✅ Whisper ASR integration (faster-whisper ưu tiên)
- ✅ Vietnamese interference rules
- ✅ Health checks (ready/live/health)
- ✅ CORS configuration

### AI Core (60%)
- ✅ L2-ARCTIC data extraction script (HOẠT ĐỘNG - 4910 lỗi)
- ✅ Training config (YAML)
- ✅ Evaluation framework
- ✅ WER calculation (đúng thuật toán)
- ✅ Data preparation pipeline
- ✅ Experiment tracking setup (MLflow + W&B)

### MCP Server (70%)
- ✅ MCP protocol implementation
- ✅ 4 tools registered
- ✅ Dual transport (stdio + HTTP)
- ✅ Claude Desktop config
- ✅ Vietnamese phoneme feedback database

### Testing (55%)
- ✅ Test structure (unit/integration/e2e)
- ✅ Shared fixtures
- ✅ Mock-based unit tests
- ✅ Vietnamese interference test cases
- ✅ pytest configuration

### Documentation (80%)
- ✅ Comprehensive README
- ✅ 4 ADRs (Architecture Decision Records)
- ✅ Architecture diagrams
- ✅ MCP documentation
- ✅ Docs folder structure

---

## 10. Đánh Giá: Những Gì Còn Thiếu ❌

### 🔴 Critical (Cần làm ngay)

#### 1. GOP Scoring thực sự chưa implement
**File:** `apps/backend/src/services/pronunciation.py` → `_calculate_scores()`

Hiện tại chỉ dùng `SequenceMatcher` so sánh text. Cần implement:
- **Forced Alignment**: dùng Wav2Vec2 để align audio với phonemes
- **GOP (Goodness of Pronunciation)**: tính log-posterior probability cho mỗi phoneme
- **Phoneme-level scoring**: điểm cho từng âm, không chỉ overall

```python
# Hiện tại (placeholder):
similarity = SequenceMatcher(None, reference, transcription).ratio()
overall = similarity * 100

# Cần implement (actual GOP):
# 1. Forced alignment: align audio frames → phonemes
# 2. GOP score = log P(phone_correct | acoustic_features)
# 3. So sánh với native speaker baseline
```

#### 2. Phoneme-level analysis chưa có
**File:** `apps/backend/src/services/pronunciation.py` → `_generate_feedback()`

Feedback hiện tại chỉ dựa trên text detection ("th" in text). Cần:
- Actual phoneme alignment
- Per-phoneme GOP scores
- Cụ thể phoneme nào sai, sai thế nào, sửa ra sao

#### 3. MCP Tools chưa kết nối Backend
**File:** `mcp/src/tools.py`

Tất cả tools trả về hardcoded data. Cần:
```python
# Thay vì:
result = {"success": True, "transcription": "hardcoded text"}

# Cần:
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{config.BACKEND_URL}/api/pronunciation/analyze",
        files={"audio": audio_bytes},
        data={"reference_text": reference_text}
    )
    result = response.json()
```

#### 4. Database chưa implement
Config có `DATABASE_URL` và `REDIS_URL` nhưng:
- Chưa có SQLAlchemy models
- Chưa có Alembic migrations
- Chưa có database tables cho:
  - Users
  - Practice sessions
  - Score history
  - Progress tracking

#### 5. Authentication chưa implement
Config có `SECRET_KEY` và `ACCESS_TOKEN_EXPIRE_MINUTES` nhưng:
- Chưa có login/register endpoints
- Chưa có JWT middleware
- Frontend có interceptor cho token nhưng không có auth flow

### 🟡 Important (Nên làm sớm)

#### 6. Train.py model là placeholder
- `PronunciationScorer` dùng Linear layers đơn giản thay vì Wav2Vec2
- Chưa load actual audio features
- Dataset trả về random tensors

#### 7. .env file chưa có
Nhiều settings cần `.env` file:
```env
SECRET_KEY=actual-secret-key
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
WHISPER_MODEL=base
USE_GPU=false
```

#### 8. Frontend thiếu nhiều tính năng
- ❌ Không có login/register page
- ❌ Không có progress tracking UI
- ❌ Không có history page
- ❌ Không có dark mode toggle (CSS có nhưng UI không có)
- ❌ Không có loading skeleton
- ❌ Không có error boundary
- ❌ Chỉ có 3 câu mẫu hardcoded

#### 9. WebSocket chưa implement
README mentions "Real-time Feedback" nhưng chưa có WebSocket:
- Streaming transcription
- Real-time waveform visualization
- Live pronunciation scoring during speech

#### 10. CI/CD Pipeline chưa có
- ❌ Không có `.github/workflows/` directory
- ❌ README badge link tới workflow không tồn tại
- Cần: lint → test → build → deploy pipeline

### 🟢 Nice to Have (Cải thiện thêm)

#### 11. Monitoring chưa implement
requirements.txt có `prometheus-client` và `opentelemetry` nhưng:
- Chưa có metrics endpoints
- Chưa có tracing
- Chưa có alerting

#### 12. Caching chưa implement
- Redis configured nhưng chưa dùng
- Nên cache: model predictions, transcriptions

#### 13. Celery task queue chưa implement
- requirements.txt có `celery` nhưng chưa dùng
- Audio processing nặng nên chạy async via queue

#### 14. `packages/shared-types/` chưa tạo
README có mention nhưng folder chưa tồn tại.

#### 15. Notebooks chưa có
`ai-core/notebooks/` trong README nhưng chưa tạo:
- EDA (Exploratory Data Analysis)
- Model experiments
- Error analysis visualization

#### 16. Mobile app
README mentions future Mobile App nhưng chưa có codebase.

---

## 11. Roadmap Đề Xuất

### Phase 1: Core ML Pipeline (Ưu tiên cao nhất)

```
Tuần 1-2: Implement GOP Scoring
├── Nghiên cứu: Kaldi GOP, Wav2Vec2 forced alignment
├── Implement forced alignment dùng torchaudio
├── Tính GOP scores cho từng phoneme
├── Test với L2-ARCTIC data (4910 lỗi)
└── Cập nhật PronunciationService._calculate_scores()

Tuần 3-4: Phoneme-Level Analysis
├── Integrate G2P (Grapheme-to-Phoneme) 
├── Phoneme alignment visualization
├── Per-phoneme feedback generation
└── Cập nhật PronunciationService._generate_feedback()
```

### Phase 2: Connect Everything

```
Tuần 5: MCP ↔ Backend Integration
├── Tools gọi Backend API thực
├── Error handling
└── Test end-to-end

Tuần 6: Database & Auth
├── SQLAlchemy models
├── Alembic migrations
├── JWT authentication
├── User registration/login
└── Practice history tracking
```

### Phase 3: Polish

```
Tuần 7-8: Frontend Enhancement
├── Login/Register pages
├── History dashboard
├── More practice phrases
├── Progress charts
├── Dark mode toggle
└── Error boundaries

Tuần 9-10: DevOps
├── GitHub Actions CI/CD
├── .env templates
├── Prometheus metrics
├── Health check improvements
└── Documentation updates
```

---

## Tóm Tắt

| Mục | Điểm | Ghi chú |
|-----|-------|---------|
| Architecture | 9/10 | Rất tốt, chuyên nghiệp |
| Frontend | 7/10 | Core OK, thiếu nhiều pages |
| Backend | 6/10 | API OK, scoring là placeholder |
| AI Core | 5/10 | Data extraction tốt, model chưa thực |
| MCP | 6/10 | Structure tốt, chưa kết nối |
| Testing | 5/10 | Framework tốt, coverage thấp |
| Infrastructure | 8/10 | Docker rất tốt |
| Documentation | 8/10 | ADRs chuyên nghiệp |
| **Tổng** | **6.75/10** | **Skeleton tốt, cần fill in thực** |

**Nhận xét chung:** Hệ thống có kiến trúc rất chuyên nghiệp và "production-ready" về mặt structure. Tuy nhiên, phần **core value** - tức là chấm điểm phát âm (GOP scoring) - hiện vẫn là placeholder. Đây là phần quan trọng nhất cần implement để biến dự án từ "demo" thành "working product".
