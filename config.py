import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration manager for the multi-agent system.
    Loads settings from environment variables and .env files.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
    
    @property
    def serp_api_key(self) -> str:
        """Get Serp API key from environment."""
        api_key = os.getenv("SERP_API_KEY")
        if not api_key:
            raise ValueError("SERP_API_KEY environment variable is not set.")
        return api_key
    
    @property
    def search_agent_config(self) -> Dict[str, Any]:
        """Get search agent configuration."""
        return {
            "timeout": int(os.getenv("SEARCH_TIMEOUT", 15)),
            "max_results": int(os.getenv("SEARCH_MAX_RESULTS", 10))
        }
    
    @property
    def groq_api_key(self) -> str:
        """Get Groq API key from environment."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        return api_key
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv("LOG_LEVEL", "INFO")
    