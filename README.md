# 🎤 VietSpeak AI - English Speaking Practice for Vietnamese Learners

[![CI/CD](https://github.com/your-username/vietspeak-ai/workflows/CI/CD/badge.svg)](https://github.com/your-username/vietspeak-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> An AI-powered English speaking practice application specifically designed for Vietnamese learners, featuring pronunciation scoring and real-time feedback.

## 🎯 Project Overview

This is a **research portfolio project** for AI Lab application (Prof. Vivian's Lab, Taiwan), demonstrating:
- Deep technical thinking in AI/ML system design
- Enterprise-grade monorepo architecture
- Production-ready MLOps practices

### Phase 1 Focus: Speaking Pipeline
- Audio Processing & Feature Extraction
- Speech-to-Text (ASR) with Vietnamese accent adaptation
- Pronunciation Scoring & Feedback Generation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│              Audio Recording │ Real-time Feedback                │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST/WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                           │
│         Audio Processing │ API Gateway │ MCP Server              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    AI Core (ML Pipeline)                         │
│     ASR Model │ Pronunciation Scorer │ Feedback Generator        │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
vietspeak-ai/
├── apps/                    # Application services
│   ├── frontend/           # Next.js web application
│   └── backend/            # FastAPI backend service
├── packages/               # Shared packages
│   └── shared-types/       # Shared TypeScript/Python types
├── ai-core/                # AI Research & ML Pipeline
│   ├── data/              # Datasets (VIVOS, custom)
│   ├── models/            # Trained models & configs
│   ├── notebooks/         # Research experiments
│   ├── src/               # ML source code
│   └── scripts/           # Training & evaluation scripts
├── mcp/                    # Model Context Protocol Server
├── tests/                  # Comprehensive testing suite
├── infra/                  # Infrastructure & deployment
├── docs/                   # Documentation
└── .github/               # CI/CD workflows
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- CUDA 11.8+ (for GPU training)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/vietspeak-ai.git
cd vietspeak-ai

# Setup with make
make setup

# Or manually:
# 1. Setup Python environment
cd ai-core && python -m venv venv && pip install -r requirements.txt

# 2. Setup Frontend
cd apps/frontend && npm install

# 3. Setup Backend
cd apps/backend && pip install -r requirements.txt

# 4. Start development
docker-compose -f infra/docker/docker-compose.dev.yml up
```

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests
make test-unit

# Integration tests
make test-integration

# Model evaluation
make eval-model
```

## 📚 Documentation

- [Architecture Decision Records](docs/architecture/README.md)
- [API Documentation](docs/api/README.md)
- [Model Documentation](docs/models/README.md)
- [Setup Guide](docs/setup/README.md)

## 🔬 Research Focus

This project explores:
1. **Vietnamese-accented English ASR**: Adapting models for L1 Vietnamese interference
2. **Pronunciation Assessment**: GOP-based scoring with phoneme-level feedback
3. **MCP Integration**: Enabling LLM clients to access pronunciation tools

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Your Name**
- Portfolio: [your-portfolio.com](https://your-portfolio.com)
- Research Interest: Speech AI, MLOps, Human-Computer Interaction
