# =============================================================================
# MCP Server Configuration
# =============================================================================

from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """Configuration for the MCP Server."""
    
    # Server Info
    SERVER_NAME: str = "vietspeak-pronunciation"
    SERVER_VERSION: str = "0.1.0"
    
    # Backend Connection
    BACKEND_URL: str = "http://localhost:8000"
    
    # Audio Settings
    MAX_AUDIO_SIZE_MB: int = 10
    SUPPORTED_FORMATS: list = ["wav", "mp3", "webm", "ogg"]
    
    # Timeouts
    REQUEST_TIMEOUT: int = 30
    
    class Config:
        env_prefix = "MCP_"
        env_file = ".env"


config = MCPConfig()
