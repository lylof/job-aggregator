"""
Migration helper for transitioning from old config structure to new layered architecture.
This file helps convert existing source configurations to the new format.
"""

from typing import Dict, Any, Optional
from .base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, JinaReaderTechnicalConfig,
    DEFAULT_TECHNICAL_CONFIG, SourceType
)


def migrate_old_source_config(old_config: Dict[str, Any]) -> tuple[SourceStage1Config, Optional[SourceStage2Config]]:
    """
    Migrate old source configuration format to new layered architecture.
    
    Args:
        old_config: Dictionary containing old configuration format
        
    Returns:
        Tuple of (Stage1Config, Stage2Config or None)
    """
    
    # Create base source config
    base_config = SourceBaseConfig(
        name=old_config.get("name", ""),
        base_url=old_config.get("base_url", ""),
        listing_url=old_config.get("listing_url", ""),
        source_type=SourceType(old_config.get("source_type", "private")),
        disabled=old_config.get("disabled", False),
        url_patterns=old_config.get("url_patterns", []),
        request_delay=old_config.get("request_delay", 1.0),
        requires_headers=old_config.get("requires_headers", False),
        custom_headers=old_config.get("custom_headers", {}),
        expected_jobs_per_page=old_config.get("expected_jobs_per_page", 20),
        reliability_score=old_config.get("reliability_score", 0.8)
    )
    
    # Create Stage 1 configuration
    stage1_jina_config = Stage1JinaConfig(base=DEFAULT_TECHNICAL_CONFIG)
    
    stage1_config = SourceStage1Config(
        base=base_config,
        jina_config=stage1_jina_config,
        css_selector_jobs=old_config.get("css_selector_jobs"),
        pagination_pattern=old_config.get("pagination_pattern"),
        max_pages=old_config.get("max_pages", 10),
        jina_params=old_config.get("jina_params", {})
    )
    
    # Create Stage 2 configuration if stage2_params exists
    stage2_config = None
    if "stage2_params" in old_config and old_config["stage2_params"]:
        stage2_params = old_config["stage2_params"]
        
        stage2_jina_config = Stage2JinaConfig(base=DEFAULT_TECHNICAL_CONFIG)
        
        stage2_config = SourceStage2Config(
            base=base_config,
            jina_config=stage2_jina_config,
            enabled=stage2_params.get("enabled", False),
            css_selector_exclude=old_config.get("css_selector_exclude"),
            jina_params=stage2_params.get("jina_params", {}),
            gemini_config=stage2_params.get("gemini_config", {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            })
        )
    
    return stage1_config, stage2_config


def create_backward_compatible_config(stage1_config: SourceStage1Config, 
                                    stage2_config: Optional[SourceStage2Config] = None) -> Dict[str, Any]:
    """
    Create a backward-compatible configuration dictionary from new config objects.
    This helps maintain compatibility with existing code during transition.
    
    Args:
        stage1_config: Stage 1 configuration
        stage2_config: Optional Stage 2 configuration
        
    Returns:
        Dictionary in old configuration format
    """
    
    base = stage1_config.base
    
    # Build backward-compatible dictionary
    compat_config = {
        "name": base.name,
        "base_url": base.base_url,
        "listing_url": base.listing_url,
        "source_type": base.source_type,
        "disabled": base.disabled,
        "url_patterns": base.url_patterns,
        "request_delay": base.request_delay,
        "requires_headers": base.requires_headers,
        "custom_headers": base.custom_headers,
        "expected_jobs_per_page": base.expected_jobs_per_page,
        "reliability_score": base.reliability_score,
        
        # Stage 1 specific
        "css_selector_jobs": stage1_config.css_selector_jobs,
        "pagination_pattern": stage1_config.pagination_pattern,
        "max_pages": stage1_config.max_pages,
        "jina_params": stage1_config.jina_params,
    }
    
    # Add Stage 2 parameters if available
    if stage2_config:
        compat_config.update({
            "css_selector_exclude": stage2_config.css_selector_exclude,
            "use_reader_lm": True,  # Default for backward compatibility
            "stage2_params": {
                "enabled": stage2_config.enabled,
                "jina_params": stage2_config.jina_params,
                "gemini_config": stage2_config.gemini_config
            }
        })
    
    return compat_config


class ConfigAdapter:
    """
    Adapter class to provide backward compatibility during migration.
    Wraps new configuration objects and provides old-style interface.
    """
    
    def __init__(self, stage1_config: SourceStage1Config, stage2_config: Optional[SourceStage2Config] = None):
        self.stage1_config = stage1_config
        self.stage2_config = stage2_config
        self._compat_dict = create_backward_compatible_config(stage1_config, stage2_config)
    
    def __getattr__(self, name: str) -> Any:
        """Provide attribute access to old-style configuration."""
        if name in self._compat_dict:
            return self._compat_dict[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get_jina_params(self, base_config=None) -> Dict[str, Any]:
        """Backward compatible method for getting Jina parameters."""
        return self.stage1_config.get_jina_params()
    
    def get_stage2_jina_params(self) -> Dict[str, Any]:
        """Backward compatible method for getting Stage 2 Jina parameters."""
        if self.stage2_config:
            return self.stage2_config.get_jina_params()
        
        # Fallback for sources without Stage 2 config
        return {
            "css_selector_excluding": "header, footer, .ads, .sidebar",
            "timeout": "45",
            "with_generated_alt": "true"
        }
    
    def get_stage2_gemini_config(self) -> Dict[str, Any]:
        """Backward compatible method for getting Gemini configuration."""
        if self.stage2_config:
            return self.stage2_config.get_gemini_config()
        
        return {
            "model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 2048
        }
    
    def is_stage2_enabled(self) -> bool:
        """Backward compatible method for checking Stage 2 status."""
        return self.stage2_config.is_enabled() if self.stage2_config else False
    
    def validate(self) -> bool:
        """Backward compatible validation method."""
        return self.stage1_config.validate()