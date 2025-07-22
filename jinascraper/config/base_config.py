"""Base configuration classes for Jina Job Scraper."""

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
class JinaReaderBaseConfig:
    """Base configuration for Jina Reader shared by all sources."""
    
    # Common Jina Reader parameters
    timeout: int = 30
    retry_attempts: int = 3
    with_images: bool = False
    with_links: bool = True
    
    # Stage 1 (Exploration) parameters
    gather_all_links_at_the_end: bool = True
    remove_all_images: bool = True
    
    # Stage 2 (Analysis) parameters
    use_reader_lm_v2: bool = True
    with_generated_alt: bool = True
    
    # CSS selectors
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
class SourceBaseConfig:
    """Base configuration for a job source."""
    
    # Basic information
    name: str
    base_url: str
    listing_url: str
    source_type: SourceType
    disabled: bool = False
    
    # Jina Reader parameters
    jina_params: Dict[str, Any] = field(default_factory=dict)
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs: Optional[str] = None
    pagination_pattern: Optional[str] = None
    max_pages: int = 10
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude: Optional[str] = None
    use_reader_lm: bool = True
    
    # URL extraction patterns
    url_patterns: List[str] = field(default_factory=list)
    
    # Site-specific settings
    request_delay: float = 1.0
    requires_headers: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Quality indicators
    expected_jobs_per_page: int = 20
    reliability_score: float = 0.8  # 0.0 to 1.0
    
    def get_jina_params(self, base_config: JinaReaderBaseConfig) -> Dict[str, Any]:
        """
        Merge base Jina Reader configuration with source-specific parameters.
        
        Args:
            base_config: Base configuration to merge with
            
        Returns:
            Merged parameters dictionary
        """
        # Start with base configuration
        params = base_config.to_dict()
        
        # Override with source-specific parameters
        for key, value in self.jina_params.items():
            params[key] = value
        
        # Add CSS selectors if defined
        if self.css_selector_jobs and "css_selector_only" not in params:
            params["css_selector_only"] = self.css_selector_jobs
            
        if self.css_selector_exclude and "css_selector_excluding" not in params:
            params["css_selector_excluding"] = self.css_selector_exclude
        
        return params
    
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


# Default Jina Reader configuration
JINA_BASE_CONFIG = JinaReaderBaseConfig(
    timeout=30,
    retry_attempts=3,
    with_images=False,
    with_links=True,
    gather_all_links_at_the_end=True,
    remove_all_images=True,
    use_reader_lm_v2=True,
    with_generated_alt=True,
    css_selector_excluding="header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
)