# Setup Guide

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 24+ (with Docker Compose)
- **CUDA**: 11.8+ (optional, for GPU training)

## Quick Start (Docker)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/your-username/vietspeak-ai.git
cd vietspeak-ai

# Start all services
docker-compose -f infra/docker/docker-compose.dev.yml up

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
# MLflow: http://localhost:5000
```

## Local Development Setup

### 1. Backend Setup

```bash
# Navigate to backend
cd apps/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run database migrations (if applicable)
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to frontend
cd apps/frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit with your API URL

# Start development server
npm run dev
```

### 3. AI Core Setup

```bash
# Navigate to AI core
cd ai-core

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download models (optional, will auto-download on first use)
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

### 4. MCP Server Setup

```bash
# Navigate to MCP server
cd mcp

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.server
```

For Claude Desktop integration, see [mcp/README.md](../mcp/README.md).

## Environment Variables

### Backend (.env)

```env
# Application
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vietspeak

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Models
WHISPER_MODEL=base
USE_GPU=false

# Security
SECRET_KEY=your-secret-key-here
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running Tests

```bash
# All tests
make test

# Backend unit tests
cd apps/backend && pytest tests/unit -v

# Frontend tests
cd apps/frontend && npm run test

# E2E tests
npm run test:e2e
```

## Common Issues

### 1. CUDA not found
```
Solution: Install CUDA toolkit or set USE_GPU=false
```

### 2. Audio processing errors
```
Solution: Install ffmpeg
- macOS: brew install ffmpeg
- Ubuntu: apt install ffmpeg
- Windows: Download from ffmpeg.org
```

### 3. Model download slow
```
Solution: Models are cached in ~/.cache/huggingface/
Pre-download: python scripts/download_models.py
```

## Next Steps

- [Development Guide](development.md)
- [Production Deployment](production.md)
- [API Documentation](../api/README.md)
