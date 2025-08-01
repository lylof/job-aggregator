"""Configuration package for Jina Job Scraper."""

# Import base configurations first
from .base_config import (
    # New layered architecture
    JinaReaderTechnicalConfig,
    Stage1JinaConfig,
    Stage2JinaConfig,
    SourceBaseConfig,
    SourceStage1Config,
    SourceStage2Config,
    SourceType,
    
    # Default configurations
    DEFAULT_TECHNICAL_CONFIG,
    DEFAULT_STAGE1_CONFIG,
    DEFAULT_STAGE2_CONFIG,
    
    # Backward compatibility
    JINA_BASE_CONFIG
)

# Import migration helper
from .migration_helper import migrate_old_source_config, ConfigAdapter

# Import settings
from .settings import config

# Import registry
from .source_registry import SourceRegistry

# Import and run initialization last
from .initialize import initialize_registry

__all__ = [
    # New architecture
    "JinaReaderTechnicalConfig",
    "Stage1JinaConfig", 
    "Stage2JinaConfig",
    "SourceBaseConfig",
    "SourceStage1Config",
    "SourceStage2Config",
    "SourceType",
    
    # Default configurations
    "DEFAULT_TECHNICAL_CONFIG",
    "DEFAULT_STAGE1_CONFIG", 
    "DEFAULT_STAGE2_CONFIG",
    
    # Migration helpers
    "migrate_old_source_config",
    "ConfigAdapter",
    
    # Registry and initialization
    "SourceRegistry",
    "initialize_registry",
    "config",
    
    # Backward compatibility
    "JINA_BASE_CONFIG"
]