"""
DEPRECATED: This module is deprecated and will be removed in a future version.
Please use the new configuration architecture in the `config` package instead.
"""

import warnings
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import the new configuration architecture
from jinascraper.config import SourceRegistry, SourceBaseConfig, SourceType

# Show deprecation warning
warnings.warn(
    "The `sources_config.py` module is deprecated and will be removed in a future version. "
    "Please use the new configuration architecture in the `config` package instead.",
    DeprecationWarning,
    stacklevel=2
)


class SourceType(str, Enum):
    """Types of job sources."""
    GOVERNMENT = "government"
    PRIVATE = "private"
    INTERNATIONAL = "international"
    NGO = "ngo"


@dataclass
class SourceConfig:
    """Configuration for a specific job source."""
    name: str
    base_url: str
    listing_url: str
    source_type: SourceType
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs: Optional[str] = None
    pagination_pattern: Optional[str] = None
    max_pages: int = 10
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude: Optional[str] = None
    use_reader_lm: bool = True
    
    # Site-specific settings
    request_delay: float = 1.0
    requires_headers: bool = False
    custom_headers: Optional[Dict[str, str]] = None
    
    # Quality indicators
    expected_jobs_per_page: int = 20
    reliability_score: float = 0.8  # 0.0 to 1.0
    disabled: bool = False  # Allow disabling sources temporarily


class TogoJobSources:
    """Configuration for all Togo job sources."""
    
    SOURCES: Dict[str, SourceConfig] = {
        "emploi_tg": SourceConfig(
            name="Emploi.tg",
            base_url="https://www.emploi.tg",
            listing_url="https://www.emploi.tg/recherche-jobs-togo",
            source_type=SourceType.PRIVATE,
            css_selector_jobs="a[href*='offre']",
            css_selector_exclude="header, footer, .ads, .sidebar, .social-share",
            max_pages=20,
            expected_jobs_per_page=15,
            reliability_score=0.9,
            request_delay=1.5
        ),
        
        "emploitogo_info": SourceConfig(
            name="EmploiTogo.info",
            base_url="https://www.emploitogo.info",
            listing_url="https://www.emploitogo.info/emploitogo/",
            source_type=SourceType.PRIVATE,
            css_selector_jobs="h3.job-title a, h3.entry-title a",
            css_selector_exclude="header, footer, .pub, .advertisement",
            max_pages=15,
            expected_jobs_per_page=12,
            reliability_score=0.8,
            request_delay=1.0
        ),
        
        "yop_lfrii": SourceConfig(
            name="YOP L-FRII",
            base_url="https://yop.l-frii.com",
            listing_url="https://yop.l-frii.com/offres-demplois/",
            source_type=SourceType.NGO,
            css_selector_jobs="h2.elementor-heading-title a",
            css_selector_exclude="header, footer, .menu, .navigation",
            max_pages=83,  # Site has extensive pagination
            expected_jobs_per_page=10,
            reliability_score=0.85,
            request_delay=2.0,  # Slower to be respectful
            custom_headers={
                "User-Agent": "Mozilla/5.0 (compatible; JinaJobScraper/1.0; +https://emploi.tg/bot)"
            }
        ),
        
        "anpe_togo": SourceConfig(
            name="ANPE Togo",
            base_url="https://anpetogo.org",
            listing_url="https://anpetogo.org/espace-chercheur-d-emploi/nos-offres-demplois",  # Sans slash final
            source_type=SourceType.GOVERNMENT,
            css_selector_jobs=".jobsearch-joblisting-classic-wrap h2 a",
            css_selector_exclude="header, footer, .menu-principal, .sidebar",
            max_pages=50,  # Government site with many offers
            expected_jobs_per_page=15,  # Basé sur les tests récents
            reliability_score=0.95,  # High reliability for government source
            request_delay=1.0
        ),
        
        "linkedin_togo": SourceConfig(
            name="LinkedIn Togo",
            base_url="https://tg.linkedin.com",
            listing_url="https://tg.linkedin.com/jobs/search?location=Togo&geoId=103603395&f_TPR=r86400&currentJobId=&position=1&pageNum=0",
            source_type=SourceType.INTERNATIONAL,
            css_selector_jobs=".base-card__full-link",
            css_selector_exclude=".global-nav, .global-footer, .ad-banner",
            max_pages=10,
            expected_jobs_per_page=25,
            reliability_score=0.9,
            request_delay=2.0,  # LinkedIn has strict rate limiting
            requires_headers=True,
            custom_headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
            }
        ),
        
        "indeed_togo": SourceConfig(
            name="Indeed Togo",
            base_url="https://fr.indeed.com",
            listing_url="https://fr.indeed.com/q-togo,-lomé-emplois.html",
            source_type=SourceType.INTERNATIONAL,
            css_selector_jobs=".job_seen_beacon, .slider_container .slider_item",
            css_selector_exclude="#searchform, .np-footer, .jobsearch-SerpJobCard-footer",
            max_pages=20,
            expected_jobs_per_page=15,
            reliability_score=0.85,
            request_delay=1.5,
            requires_headers=True,
            custom_headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9"
            },
            disabled=True  # Temporairement désactivé - protections anti-bot trop strictes
        )
    }
    
    @classmethod
    def get_source(cls, source_name: str) -> Optional[SourceConfig]:
        """Get configuration for a specific source."""
        # Try to get from new architecture first
        new_config = SourceRegistry.get_source(source_name)
        if new_config:
            # Convert to old format for backward compatibility
            return SourceConfig(
                name=new_config.name,
                base_url=new_config.base_url,
                listing_url=new_config.listing_url,
                source_type=SourceType(new_config.source_type.value),
                css_selector_jobs=new_config.css_selector_jobs,
                pagination_pattern=new_config.pagination_pattern,
                max_pages=new_config.max_pages,
                css_selector_exclude=new_config.css_selector_exclude,
                use_reader_lm=new_config.use_reader_lm,
                request_delay=new_config.request_delay,
                requires_headers=new_config.requires_headers,
                custom_headers=new_config.custom_headers,
                expected_jobs_per_page=new_config.expected_jobs_per_page,
                reliability_score=new_config.reliability_score,
                disabled=new_config.disabled
            )
        
        # Fall back to old format
        return cls.SOURCES.get(source_name)
    
    @classmethod
    def get_all_sources(cls) -> Dict[str, SourceConfig]:
        """Get all source configurations."""
        # Merge old and new sources
        sources = cls.SOURCES.copy()
        
        # Add sources from new architecture
        for source_id, new_config in SourceRegistry.get_all_sources().items():
            if source_id not in sources:
                # Convert to old format
                sources[source_id] = SourceConfig(
                    name=new_config.name,
                    base_url=new_config.base_url,
                    listing_url=new_config.listing_url,
                    source_type=SourceType(new_config.source_type.value),
                    css_selector_jobs=new_config.css_selector_jobs,
                    pagination_pattern=new_config.pagination_pattern,
                    max_pages=new_config.max_pages,
                    css_selector_exclude=new_config.css_selector_exclude,
                    use_reader_lm=new_config.use_reader_lm,
                    request_delay=new_config.request_delay,
                    requires_headers=new_config.requires_headers,
                    custom_headers=new_config.custom_headers,
                    expected_jobs_per_page=new_config.expected_jobs_per_page,
                    reliability_score=new_config.reliability_score,
                    disabled=new_config.disabled
                )
        
        return sources
    
    @classmethod
    def get_active_sources(cls) -> Dict[str, SourceConfig]:
        """Get only active (non-disabled) source configurations."""
        return {
            name: config for name, config in cls.get_all_sources().items()
            if not getattr(config, 'disabled', False)
        }
    
    @classmethod
    def get_sources_by_type(cls, source_type: SourceType) -> Dict[str, SourceConfig]:
        """Get sources filtered by type."""
        return {
            name: config for name, config in cls.get_all_sources().items()
            if config.source_type == source_type
        }
    
    @classmethod
    def get_priority_sources(cls) -> List[str]:
        """Get sources ordered by reliability score (highest first)."""
        return sorted(
            cls.get_all_sources().keys(),
            key=lambda name: cls.get_all_sources()[name].reliability_score,
            reverse=True
        )
    
    @classmethod
    def validate_source_config(cls, source_name: str) -> bool:
        """Validate that a source configuration is complete."""
        config = cls.get_source(source_name)
        if not config:
            return False
        
        required_fields = [
            config.name, config.base_url, config.listing_url
        ]
        
        return all(field for field in required_fields)


# Convenience functions for common operations
def get_togo_source_names() -> List[str]:
    """Get list of all Togo job source names."""
    return list(TogoJobSources.get_all_sources().keys())


def get_government_sources() -> Dict[str, SourceConfig]:
    """Get only government job sources."""
    return TogoJobSources.get_sources_by_type(SourceType.GOVERNMENT)


def get_international_sources() -> Dict[str, SourceConfig]:
    """Get only international job sources (LinkedIn, Indeed)."""
    return TogoJobSources.get_sources_by_type(SourceType.INTERNATIONAL)


def get_source_config(source_name: str) -> Optional[SourceConfig]:
    """Get configuration for a specific source."""
    return TogoJobSources.get_source(source_name)