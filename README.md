# 🎓 VietSpeak AI — IELTS Speaking Evaluator for Vietnamese Learners

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

> An AI-powered web app that helps Vietnamese learners practise **IELTS Speaking**.
> Record an answer in the browser — the app transcribes your speech, corrects likely
> mishearings, and grades your **Lexical Resource** and **Grammar** on the IELTS 0–9
> band scale, with examiner-style feedback.

## 🎯 Project Overview

A **research portfolio project** (AI Lab application — Prof. Vivian's Lab, Taiwan)
demonstrating end-to-end AI system design: a working speaking-assessment product on
top of cloud speech + LLM models, plus a research track on **Vietnamese-accented
English ASR** (fine-tuning Whisper on the L2-ARCTIC corpus).

## ✨ Features

- 🎙️ **In-browser recording** via the MediaRecorder API (16 kHz mono, noise-suppressed).
- 🗣️ **Speech-to-Text** using Groq Cloud **Whisper `large-v3`**, with hallucination
  detection on silent audio.
- 🧠 **IELTS evaluation** using Groq Cloud **Llama 3.3 70B**: corrected transcript,
  Lexical Resource score (0–9), Grammar score (0–9), and written feedback.
- 🎲 **Random IELTS prompts** (Part 1 / 2 / 3) served from the database.
- 💾 **Attempt history** persisted to the database.
- 🔁 **Resilient database**: prefers Supabase Postgres, automatically falls back to a
  bundled local SQLite database when the cloud DB is unreachable — so the app keeps
  working offline.
- 🔬 **Research track** (`ai-core/`): scripts to fine-tune Whisper-small on L2-ARCTIC
  for Vietnamese-accent adaptation, plus baseline/evaluation tooling.

## 🏗️ Architecture

```
┌─────────────────────────┐      /api proxy       ┌──────────────────────────┐
│  Frontend (Next.js 14)   │ ───────────────────►  │   Backend (FastAPI)       │
│  localhost:3000          │                       │   localhost:8000          │
└─────────────────────────┘                       └────────────┬─────────────┘
                                                                │
                                  ┌─────────────────────────────┼───────────────────────┐
                                  ▼                             ▼                         ▼
                        ┌──────────────────┐         ┌──────────────────┐     ┌────────────────────┐
                        │ Groq Whisper STT │         │ Groq Llama 3.3   │     │ DB: Supabase PG    │
                        │ (transcription)  │         │ (IELTS scoring)  │     │ → SQLite fallback  │
                        └──────────────────┘         └──────────────────┘     └────────────────────┘
```

### Tech stack

| Layer    | Technology                                                       |
|----------|------------------------------------------------------------------|
| Frontend | Next.js 14, React 18, TailwindCSS, TanStack Query, Axios          |
| Backend  | FastAPI, Pydantic, SQLAlchemy, Uvicorn                            |
| AI       | Groq Cloud — Whisper `large-v3`, Llama 3.3 70B                    |
| Database | Supabase Postgres (primary) · SQLite (local fallback)            |
| AI Core  | PyTorch, Hugging Face Transformers — Whisper fine-tuning on L2-ARCTIC |

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ and Node.js 18+
- A free [Groq API key](https://console.groq.com/keys)

### 1. Backend

```bash
cd apps/backend
python -m venv .venv && .venv\Scripts\activate     # Windows (PowerShell)
pip install -r requirements.txt

# Configure environment
copy .env.example .env        # then edit .env and set GROQ_API_KEY
# Optionally set DATABASE_URL to your Supabase Postgres URL.
# If omitted or unreachable, the app uses a local SQLite dev.db automatically.

# Seed IELTS prompts (static dataset, no network needed)
python -m src.seed_data

# Run the API (http://localhost:8000, interactive docs at /api/docs)
python -m uvicorn src.main:app --port 8000 --reload
```

### 2. Frontend

```bash
cd apps/frontend
npm install
npm run dev        # http://localhost:3000
```

The frontend proxies `/api/*` to the backend (`BACKEND_URL` in `.env.local`,
defaults to `http://localhost:8000`).

## 🔌 Key API Endpoints

| Method | Endpoint                  | Description                              |
|--------|---------------------------|------------------------------------------|
| GET    | `/api/v1/prompts/random`  | Return a random IELTS Speaking prompt    |
| POST   | `/api/v1/recognize`       | Transcribe an uploaded audio file        |
| POST   | `/api/v1/assess_speaking` | Full pipeline: STT → LLM scoring → save  |
| GET    | `/api/health`             | Health check                             |

Example response from `POST /api/v1/assess_speaking`:

```json
{
  "raw_transcript": "My hometown is a small city in the north of Vietnam...",
  "evaluation": {
    "corrected_text": "My hometown is a small city in the north of Vietnam...",
    "lexical_score": 6,
    "grammar_score": 8,
    "feedback": "Clear and coherent; vocabulary is somewhat basic..."
  },
  "attempt_id": 8
}
```

## 📁 Project Structure

```
speaking_app/
├── apps/
│   ├── frontend/   # Next.js web app (recording UI, score rings, feedback)
│   └── backend/    # FastAPI API (STT, LLM evaluation, prompts, DB)
├── ai-core/        # ML research: Whisper fine-tuning on L2-ARCTIC + eval scripts
├── docs/           # System analysis & tutorial
└── mcp/            # Model Context Protocol server (optional)
```

## 🔬 Research Focus

1. **Vietnamese-accented English ASR** — adapting Whisper for L1-Vietnamese interference.
2. **LLM-as-examiner** — structured IELTS scoring (Lexical / Grammar) with JSON-only output.
3. **Robust deployment** — graceful cloud-to-local database fallback.

## 👤 Author

**Đặng Quốc Hiệp**
- GitHub: [@QuocHiep123](https://github.com/QuocHiep123)
- Email: dangquochiep2908@gmail.com
- Research interest: Speech AI, MLOps, Human-Computer Interaction

## 📄 License

MIT License.
