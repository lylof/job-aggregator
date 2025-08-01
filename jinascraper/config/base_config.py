"""Base configuration classes for Jina Job Scraper - Layered Architecture."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class SourceType(str, Enum):
    """Types of job sources."""
    GOVERNMENT = "government"
    PRIVATE = "private"
    INTERNATIONAL = "international"
    NGO = "ngo"


@dataclass
class JinaReaderTechnicalConfig:
    """
    Technical configuration for Jina Reader API - shared across all stages.
    Contains only technical parameters, no business logic.
    """
    
    # Core API parameters
    timeout: int = 30
    retry_attempts: int = 3
    
    # CSS selectors (can be overridden by specific stages)
    css_selector_only: Optional[str] = None
    css_selector_excluding: Optional[str] = None
    css_selector_wait_for: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for API calls."""
        result = {}
        
        # Add all non-None parameters
        for key, value in self.__dict__.items():
            if value is not None:
                # Convert boolean values to strings for API
                if isinstance(value, bool):
                    result[key] = str(value).lower()
                else:
                    result[key] = value
        
        return result


@dataclass
class Stage1JinaConfig:
    """
    Stage 1 specific Jina Reader configuration for URL exploration/discovery.
    Inherits technical config and adds stage-specific parameters.
    """
    
    # Technical base configuration
    base: JinaReaderTechnicalConfig = field(default_factory=JinaReaderTechnicalConfig)
    
    # Stage 1 specific parameters - Paramètres généraux pour toutes les sources
    engine: str = "browser"  # X-Engine: browser
    no_cache: bool = True    # X-No-Cache: true
    retain_images: str = "none"  # X-Retain-Images: none
    with_links_summary: str = "all"  # X-With-Links-Summary: all
    
    # Stage 1 default CSS exclusions
    default_css_excluding: str = "header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
    
    def get_jina_params(self, source_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get merged Jina parameters for Stage 1 processing.
        
        Args:
            source_overrides: Source-specific parameter overrides
            
        Returns:
            Merged parameters dictionary for Jina API
        """
        # Start with technical base
        params = self.base.to_dict()
        
        # Add Stage 1 specific parameters (paramètres généraux pour toutes les sources)
        params.update({
            "engine": self.engine,  # X-Engine: browser
            "no_cache": str(self.no_cache).lower(),  # X-No-Cache: true
            "retain_images": self.retain_images,  # X-Retain-Images: none
            "with_links_summary": self.with_links_summary  # X-With-Links-Summary: all
        })
        
        # Set default CSS excluding if not already set
        if "css_selector_excluding" not in params or not params["css_selector_excluding"]:
            params["css_selector_excluding"] = self.default_css_excluding
        
        # Apply source-specific overrides
        if source_overrides:
            for key, value in source_overrides.items():
                params[key] = value
        
        return params


@dataclass
class Stage2JinaConfig:
    """
    Stage 2 specific Jina Reader configuration for detailed content extraction.
    Inherits technical config and adds stage-specific parameters.
    """
    
    # Technical base configuration
    base: JinaReaderTechnicalConfig = field(default_factory=JinaReaderTechnicalConfig)
    
    # Stage 2 specific parameters - Nouvelle stratégie robuste
    engine: str = "browser"         # X-Engine: browser
    no_cache: bool = True          # X-No-Cache: true
    return_format: str = "markdown" # X-Return-Format: markdown
    with_generated_alt: bool = True
    
    # Stage 2 optimized settings
    default_timeout: int = 30      # --max-time 30 (ajusté selon nouvelle stratégie)
    default_css_excluding: str = "header, footer, .ads, .sidebar, .comments, .related-articles"
    
    def get_jina_params(self, source_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get merged Jina parameters for Stage 2 processing.
        
        Args:
            source_overrides: Source-specific parameter overrides
            
        Returns:
            Merged parameters dictionary for Jina API
        """
        # Start with technical base
        params = self.base.to_dict()
        
        # Override timeout for Stage 2
        params["timeout"] = str(self.default_timeout)
        
        # Add Stage 2 specific parameters - Nouvelle stratégie robuste
        params.update({
            "engine": self.engine,                                    # X-Engine: browser
            "no_cache": str(self.no_cache).lower(),                  # X-No-Cache: true
            "return_format": self.return_format,                     # X-Return-Format: markdown
            "with_generated_alt": str(self.with_generated_alt).lower()
        })
        
        # Set default CSS excluding if not already set
        if "css_selector_excluding" not in params or not params["css_selector_excluding"]:
            params["css_selector_excluding"] = self.default_css_excluding
        
        # Apply source-specific overrides
        if source_overrides:
            for key, value in source_overrides.items():
                params[key] = value
        
        return params


@dataclass
class SourceBaseConfig:
    """
    Base configuration for a job source - stage-agnostic.
    Contains only common source information and technical settings.
    """
    
    # Basic source information
    name: str
    base_url: str
    listing_url: str
    source_type: SourceType
    disabled: bool = False
    
    # URL extraction patterns
    url_patterns: List[str] = field(default_factory=list)
    
    # Site-specific technical settings
    request_delay: float = 1.0
    requires_headers: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Quality indicators
    expected_jobs_per_page: int = 20
    reliability_score: float = 0.8  # 0.0 to 1.0
    
    def validate(self) -> bool:
        """
        Validate that the source configuration is complete.
        
        Returns:
            True if configuration is valid
        """
        required_fields = [
            self.name, self.base_url, self.listing_url
        ]
        
        return all(field for field in required_fields)


@dataclass
class SourceStage1Config:
    """
    Stage 1 specific configuration for a job source.
    Extends base source config with Stage 1 parameters.
    """
    
    # Base source configuration
    base: SourceBaseConfig
    
    # Stage 1 Jina configuration
    jina_config: Stage1JinaConfig = field(default_factory=Stage1JinaConfig)
    
    # Stage 1 specific parameters
    css_selector_jobs: Optional[str] = None
    pagination_pattern: Optional[str] = None
    max_pages: int = 10
    
    # Stage 1 Jina parameter overrides
    jina_params: Dict[str, Any] = field(default_factory=dict)
    
    def get_jina_params(self) -> Dict[str, Any]:
        """
        Get complete Jina parameters for Stage 1 processing.
        
        Returns:
            Merged parameters dictionary for Jina API
        """
        # Start with source-specific overrides
        overrides = self.jina_params.copy()
        
        # Add CSS selector if defined
        if self.css_selector_jobs:
            overrides["css_selector_only"] = self.css_selector_jobs
        
        # Get merged parameters from Stage 1 config
        return self.jina_config.get_jina_params(overrides)
    
    def validate(self) -> bool:
        """Validate Stage 1 configuration."""
        return self.base.validate()


@dataclass
class SourceStage2Config:
    """
    Stage 2 specific configuration for a job source.
    Extends base source config with Stage 2 parameters.
    """
    
    # Base source configuration
    base: SourceBaseConfig
    
    # Stage 2 Jina configuration
    jina_config: Stage2JinaConfig = field(default_factory=Stage2JinaConfig)
    
    # Stage 2 specific parameters
    enabled: bool = False
    css_selector_exclude: Optional[str] = None
    
    # Stage 2 Jina parameter overrides
    jina_params: Dict[str, Any] = field(default_factory=dict)
    
    # Gemini configuration for Stage 2
    gemini_config: Dict[str, Any] = field(default_factory=lambda: {
        "model": "gemini-1.5-flash",
        "temperature": 0.1,
        "max_tokens": 2048
    })
    
    def get_jina_params(self) -> Dict[str, Any]:
        """
        Get complete Jina parameters for Stage 2 processing.
        
        Returns:
            Merged parameters dictionary for Jina API
        """
        # Start with source-specific overrides
        overrides = self.jina_params.copy()
        
        # Add CSS exclusion selector if defined
        if self.css_selector_exclude:
            overrides["css_selector_excluding"] = self.css_selector_exclude
        
        # Get merged parameters from Stage 2 config
        return self.jina_config.get_jina_params(overrides)
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """Get Gemini configuration for Stage 2 processing."""
        return self.gemini_config.copy()
    
    def is_enabled(self) -> bool:
        """Check if Stage 2 processing is enabled for this source."""
        return self.enabled
    
    def validate(self) -> bool:
        """Validate Stage 2 configuration."""
        return self.base.validate()


# Default technical configuration shared across all stages
DEFAULT_TECHNICAL_CONFIG = JinaReaderTechnicalConfig(
    timeout=30,
    retry_attempts=3,
    css_selector_excluding="header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
)

# Default Stage 1 configuration avec paramètres généraux optimisés
DEFAULT_STAGE1_CONFIG = Stage1JinaConfig(
    base=DEFAULT_TECHNICAL_CONFIG,
    engine="browser",  # X-Engine: browser
    no_cache=True,     # X-No-Cache: true
    retain_images="none",  # X-Retain-Images: none
    with_links_summary="all"  # X-With-Links-Summary: all
)

# Default Stage 2 configuration - Nouvelle stratégie robuste
DEFAULT_STAGE2_CONFIG = Stage2JinaConfig(
    base=DEFAULT_TECHNICAL_CONFIG,
    engine="browser",           # X-Engine: browser
    no_cache=True,             # X-No-Cache: true
    return_format="markdown",   # X-Return-Format: markdown
    default_timeout=30,        # --max-time 30
    with_generated_alt=True    # Conserver cette option
)

# Backward compatibility - deprecated, use DEFAULT_STAGE1_CONFIG instead
JINA_BASE_CONFIG = DEFAULT_STAGE1_CONFIG