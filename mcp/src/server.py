# =============================================================================
# VietSpeak MCP Server - Main Entry Point
# =============================================================================
"""
Model Context Protocol (MCP) Server for VietSpeak AI.

This server exposes pronunciation analysis tools to MCP-compatible clients
(like Claude Desktop, Cursor, etc.), enabling LLMs to directly assess
pronunciation quality.

Protocol: MCP (Model Context Protocol)
Transport: stdio (for Claude Desktop) or HTTP/SSE (for web clients)

Usage:
    # stdio mode (for Claude Desktop)
    python -m src.server
    
    # HTTP mode (for web clients)
    python -m src.server --transport http --port 8080
"""

import asyncio
import argparse
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.tools import (
    analyze_pronunciation_tool,
    transcribe_audio_tool,
    get_phoneme_feedback_tool,
    compare_pronunciation_tool,
)
from src.config import MCPConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize MCP Server
server = Server("vietspeak-pronunciation")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available pronunciation tools.
    
    These tools can be called by any MCP client (Claude, etc.)
    to perform pronunciation analysis.
    """
    return [
        Tool(
            name="analyze_pronunciation",
            description="""
                Analyze English pronunciation from audio.
                Returns overall score, accuracy, fluency, and detailed phoneme-level feedback.
                Specifically optimized for Vietnamese English learners with L1 interference detection.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_base64": {
                        "type": "string",
                        "description": "Base64-encoded audio data (WAV, MP3, or WebM format)",
                    },
                    "reference_text": {
                        "type": "string",
                        "description": "The expected English text that should have been spoken",
                    },
                    "detailed_feedback": {
                        "type": "boolean",
                        "description": "Whether to include phoneme-level feedback",
                        "default": True,
                    },
                },
                "required": ["audio_base64", "reference_text"],
            },
        ),
        Tool(
            name="transcribe_audio",
            description="""
                Transcribe English speech audio to text using ASR.
                Returns the transcribed text with confidence scores.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_base64": {
                        "type": "string",
                        "description": "Base64-encoded audio data",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (default: 'en' for English)",
                        "default": "en",
                    },
                },
                "required": ["audio_base64"],
            },
        ),
        Tool(
            name="get_phoneme_feedback",
            description="""
                Get detailed phoneme-level pronunciation feedback.
                Compares expected phonemes with detected phonemes and provides
                specific tips for Vietnamese speakers.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "English text to analyze",
                    },
                    "detected_phonemes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of detected phonemes from speech",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="compare_pronunciation",
            description="""
                Compare two pronunciation attempts and determine improvement.
                Useful for tracking learner progress over time.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_before_base64": {
                        "type": "string",
                        "description": "Base64-encoded audio of first attempt",
                    },
                    "audio_after_base64": {
                        "type": "string",
                        "description": "Base64-encoded audio of second attempt",
                    },
                    "reference_text": {
                        "type": "string",
                        "description": "The expected English text",
                    },
                },
                "required": ["audio_before_base64", "audio_after_base64", "reference_text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.
    
    Routes tool calls to appropriate handlers and returns results.
    """
    logger.info(f"Tool called: {name}")
    
    try:
        if name == "analyze_pronunciation":
            result = await analyze_pronunciation_tool(
                audio_base64=arguments["audio_base64"],
                reference_text=arguments["reference_text"],
                detailed_feedback=arguments.get("detailed_feedback", True),
            )
        elif name == "transcribe_audio":
            result = await transcribe_audio_tool(
                audio_base64=arguments["audio_base64"],
                language=arguments.get("language", "en"),
            )
        elif name == "get_phoneme_feedback":
            result = await get_phoneme_feedback_tool(
                text=arguments["text"],
                detected_phonemes=arguments.get("detected_phonemes"),
            )
        elif name == "compare_pronunciation":
            result = await compare_pronunciation_tool(
                audio_before_base64=arguments["audio_before_base64"],
                audio_after_base64=arguments["audio_after_base64"],
                reference_text=arguments["reference_text"],
            )
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_stdio_server():
    """Run MCP server with stdio transport (for Claude Desktop)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description="VietSpeak MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port (only used with --transport http)",
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting VietSpeak MCP Server (transport: {args.transport})")
    
    if args.transport == "stdio":
        asyncio.run(run_stdio_server())
    else:
        # HTTP transport for web clients
        from src.http_server import run_http_server
        run_http_server(port=args.port)


if __name__ == "__main__":
    main()
