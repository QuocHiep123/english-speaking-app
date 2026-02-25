# ADR-003: MCP Integration Strategy

## Status
**Accepted**

## Context
We want to integrate VietSpeak AI with AI assistants (Claude) via Model Context Protocol (MCP). This enables direct pronunciation analysis through conversational AI interfaces.

## Decision Drivers
- Unique portfolio differentiator
- Future-proof architecture
- Demonstration of emerging technology expertise
- Research lab alignment (AI-focused)

## Considered Options

### Option 1: Direct Claude API Integration
- Simpler implementation
- One-way integration
- Limited tool capabilities

### Option 2: MCP Server (stdio transport)
- Native Claude Desktop integration
- Rich tool definitions
- Bidirectional communication

### Option 3: MCP Server (HTTP transport)
- Web-based Claude integration
- Broader client compatibility
- More complex setup

### Option 4: Hybrid (stdio + HTTP)
- Maximum flexibility
- Support both Claude Desktop and web clients
- Additional maintenance

## Decision
**Hybrid MCP Server (stdio + HTTP)**

## Rationale
1. **Claude Desktop**: stdio transport for local development
2. **Web Clients**: HTTP transport for production
3. **Research Value**: Demonstrates emerging protocol expertise
4. **Portfolio Impact**: Unique feature for AI lab application

## Implementation

### Tool Definitions
```python
TOOLS = [
    {
        "name": "analyze_pronunciation",
        "description": "Analyze pronunciation from audio",
        "inputSchema": {...}
    },
    {
        "name": "transcribe_audio",
        "description": "Transcribe speech to text",
        "inputSchema": {...}
    },
    {
        "name": "get_phoneme_feedback",
        "description": "Get Vietnamese-specific feedback",
        "inputSchema": {...}
    }
]
```

### Usage Flow
```
User → Claude → MCP Server → Backend API → ML Models
                    ↓
            Structured Response
                    ↓
          Claude → User (Natural Language)
```

## Consequences

### Positive
- Cutting-edge technology demonstration
- Native LLM integration
- Unique portfolio feature

### Negative
- MCP protocol still evolving
- Additional testing complexity
- Documentation requirements

## Future Considerations
- Resource endpoints for model information
- Streaming responses for real-time feedback
- Multi-turn pronunciation coaching

## Related
- MCP Specification
- Claude Desktop documentation
- ADR-001 for monorepo structure
