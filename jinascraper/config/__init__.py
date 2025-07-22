"""Configuration package for Jina Job Scraper."""

# Import base configurations first
from .base_config import (
    SourceBaseConfig,
    JinaReaderBaseConfig,
    SourceType,
    JINA_BASE_CONFIG
)

# Import settings
from .settings import config

# Import registry
from .source_registry import SourceRegistry

# Import and run initialization last
from .initialize import initialize_registry

__all__ = [
    "SourceBaseConfig",
    "JinaReaderBaseConfig",
    "SourceType",
    "JINA_BASE_CONFIG",
    "SourceRegistry",
    "initialize_registry",
    "config"
]