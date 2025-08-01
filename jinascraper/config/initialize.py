"""Initialize the source registry with all configured sources - New Architecture."""

import structlog
from .source_registry import SourceRegistry

# Import source configurations (backward compatibility adapters)
from .sources.anpetogo import ANPETOGO_CONFIG
from .sources.emploi_tg import EMPLOI_TG_CONFIG
from .sources.emploitogo_info import EMPLOITOGO_INFO_CONFIG
from .sources.yop_lfrii import YOP_LFRII_CONFIG
from .sources.linkedin_togo import LINKEDIN_TOGO_CONFIG
from .sources.indeed_togo import INDEED_TOGO_CONFIG

logger = structlog.get_logger(__name__)


def initialize_registry():
    """Initialize the source registry with all configured sources."""
    # Register all sources using backward compatibility adapters
    SourceRegistry.register_source("anpetogo", ANPETOGO_CONFIG)
    SourceRegistry.register_source("emploi_tg", EMPLOI_TG_CONFIG)
    SourceRegistry.register_source("emploitogo_info", EMPLOITOGO_INFO_CONFIG)
    SourceRegistry.register_source("yop_lfrii", YOP_LFRII_CONFIG)
    SourceRegistry.register_source("linkedin_togo", LINKEDIN_TOGO_CONFIG)
    SourceRegistry.register_source("indeed_togo", INDEED_TOGO_CONFIG)
    
    logger.info(f"Initialized source registry with {len(SourceRegistry._sources)} sources")


# Initialize the registry when the module is imported
initialize_registry()