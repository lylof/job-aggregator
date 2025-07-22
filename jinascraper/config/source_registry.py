"""Registry for job source configurations."""

from typing import Dict, List, Optional, Any
import structlog

from .base_config import SourceBaseConfig, SourceType, JINA_BASE_CONFIG

logger = structlog.get_logger(__name__)


class SourceRegistry:
    """Registry for job source configurations."""
    
    # This will be populated as source configurations are implemented
    _sources: Dict[str, SourceBaseConfig] = {}
    
    @classmethod
    def register_source(cls, source_id: str, config: SourceBaseConfig) -> None:
        """
        Register a source configuration.
        
        Args:
            source_id: Unique identifier for the source
            config: Source configuration
        """
        if source_id in cls._sources:
            logger.warning(f"Overwriting existing source configuration for {source_id}")
        
        cls._sources[source_id] = config
        logger.info(f"Registered source configuration for {source_id}")
    
    @classmethod
    def get_source(cls, source_id: str) -> Optional[SourceBaseConfig]:
        """
        Get a source configuration by ID.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Source configuration or None if not found
        """
        return cls._sources.get(source_id)
    
    @classmethod
    def get_all_sources(cls) -> Dict[str, SourceBaseConfig]:
        """
        Get all source configurations.
        
        Returns:
            Dictionary of all source configurations
        """
        return cls._sources.copy()
    
    @classmethod
    def get_active_sources(cls) -> Dict[str, SourceBaseConfig]:
        """
        Get only active (non-disabled) source configurations.
        
        Returns:
            Dictionary of active source configurations
        """
        return {
            source_id: config for source_id, config in cls._sources.items()
            if not config.disabled
        }
    
    @classmethod
    def get_sources_by_type(cls, source_type: SourceType) -> Dict[str, SourceBaseConfig]:
        """
        Get sources filtered by type.
        
        Args:
            source_type: Type of sources to filter by
            
        Returns:
            Dictionary of source configurations of the specified type
        """
        return {
            source_id: config for source_id, config in cls._sources.items()
            if config.source_type == source_type
        }
    
    @classmethod
    def get_priority_sources(cls) -> List[str]:
        """
        Get sources ordered by reliability score (highest first).
        
        Returns:
            List of source IDs ordered by reliability score
        """
        return sorted(
            cls._sources.keys(),
            key=lambda source_id: cls._sources[source_id].reliability_score,
            reverse=True
        )