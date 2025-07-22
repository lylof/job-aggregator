"""Global application settings loaded from environment variables."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger(__name__)

# Load environment variables from .env file
# Try multiple locations for the .env file
env_paths = [
    Path(__file__).parent.parent / ".env",  # jinascraper/.env
    Path(__file__).parent.parent.parent / ".env",  # root .env
    ".env"  # current directory
]

for env_path in env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded environment variables from {env_path}")
        break
else:
    logger.warning("No .env file found in expected locations")

class Config:
    """Global configuration container."""
    
    def __init__(self):
        # Jina Reader API configuration
        self.jina_api_key: str = os.getenv("JINA_API_KEY", "")
        self.jina_base_url: str = os.getenv("JINA_BASE_URL", "https://r.jina.ai")
        
        # Gemini API configuration
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        # Supabase configuration
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_key: str = os.getenv("SUPABASE_KEY", "")
        
        # Redis configuration
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_ttl_seconds: int = int(os.getenv("REDIS_TTL_SECONDS", "604800"))  # 7 days
        
        # Database configuration
        self.database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jobscraper")
        
        # Request configuration
        self.timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "60"))
        self.max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        self.request_delay_seconds: float = float(os.getenv("REQUEST_DELAY_SECONDS", "1.0"))
        
        # Scraping configuration
        self.max_urls_per_source: int = int(os.getenv("MAX_URLS_PER_SOURCE", "100"))
        self.batch_size: int = int(os.getenv("BATCH_SIZE", "10"))
        
        # Logging configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
        
        # Environment settings
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.jina_api_key:
            logger.error("JINA_API_KEY environment variable is not set")
            return False
            
        if not self.gemini_api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            return False
            
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }

# Create a singleton instance
config = Config()

# Validate configuration on import
if not config.validate():
    logger.warning("Configuration validation failed. Some features may not work correctly.")