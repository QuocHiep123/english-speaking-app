# VietSpeak MCP Server

## Overview

Model Context Protocol (MCP) server that exposes VietSpeak's pronunciation analysis capabilities to LLM clients like Claude Desktop.

## What is MCP?

MCP (Model Context Protocol) is a standard protocol that allows AI assistants (like Claude) to interact with external tools and services. By implementing an MCP server, we enable Claude and other LLM clients to directly use our pronunciation analysis tools.

## Available Tools

### 1. `analyze_pronunciation`
Analyzes English pronunciation from audio and returns detailed scores.

**Input:**
- `audio_base64`: Base64-encoded audio (WAV, MP3, WebM)
- `reference_text`: The expected English text
- `detailed_feedback`: Boolean for phoneme-level feedback

**Output:**
- Overall score (0-100)
- Accuracy, fluency, completeness scores
- Phoneme-level analysis
- Vietnamese-specific tips

### 2. `transcribe_audio`
Converts speech audio to text using ASR.

**Input:**
- `audio_base64`: Base64-encoded audio
- `language`: Language code (default: "en")

**Output:**
- Transcribed text
- Confidence score

### 3. `get_phoneme_feedback`
Provides Vietnamese-specific pronunciation guidance.

**Input:**
- `text`: English text to analyze
- `detected_phonemes`: Optional list of detected phonemes

**Output:**
- Phoneme breakdown
- Vietnamese interference patterns
- Practice suggestions

### 4. `compare_pronunciation`
Compares two pronunciation attempts for progress tracking.

**Input:**
- `audio_before_base64`: First attempt
- `audio_after_base64`: Second attempt
- `reference_text`: Expected text

**Output:**
- Score comparison
- Improvement metrics
- Specific feedback

## Setup

### For Claude Desktop

1. Copy `claude_desktop_config.json` to:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Install dependencies:
   ```bash
   cd mcp
   pip install -r requirements.txt
   ```

3. Restart Claude Desktop

### For Development

```bash
# Run in stdio mode (for testing)
python -m src.server

# Run in HTTP mode (for web clients)
python -m src.server --transport http --port 8080
```

## Architecture

```
┌─────────────────┐       MCP Protocol        ┌──────────────────┐
│  Claude Desktop │ ◄─────────────────────────► │  MCP Server     │
│  (LLM Client)   │                            │  (stdio/HTTP)   │
└─────────────────┘                            └────────┬─────────┘
                                                        │
                                                        │ HTTP
                                                        ▼
                                               ┌──────────────────┐
                                               │  Backend API     │
                                               │  (FastAPI)       │
                                               └──────────────────┘
```

## Why MCP for this project?

1. **Portfolio Value**: Demonstrates understanding of cutting-edge AI integration patterns
2. **Practical Use**: Claude can directly help users practice pronunciation
3. **Research Potential**: LLMs can orchestrate pronunciation experiments
4. **Extensibility**: Easy to add new tools as research progresses
