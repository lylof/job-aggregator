"""Configuration management for Jina Job Scraper."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class JinaScraperConfig(BaseSettings):
    """Configuration for the Jina Job Scraper service."""
    
    # Jina AI Configuration
    jina_api_key: str = Field(..., description="Jina AI API key")
    jina_base_url: str = Field(
        default="https://r.jina.ai/", 
        description="Jina Reader API base URL"
    )
    
    # Google Gemini Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-1.5-flash", 
        description="Gemini model to use"
    )
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0", 
        description="Redis connection URL"
    )
    
    # Scraping Configuration
    max_concurrent_requests: int = Field(
        default=10, 
        description="Maximum concurrent HTTP requests"
    )
    request_delay_seconds: float = Field(
        default=1.0, 
        description="Delay between requests in seconds"
    )
    retry_attempts: int = Field(
        default=3, 
        description="Number of retry attempts for failed requests"
    )
    timeout_seconds: int = Field(
        default=30, 
        description="HTTP request timeout in seconds"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    structured_logging: bool = Field(
        default=True, 
        description="Enable structured logging"
    )
    
    # Environment Settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global configuration instance
config = JinaScraperConfig()