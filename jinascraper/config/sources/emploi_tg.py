"""Configuration for Emploi.tg job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to Emploi.tg
EMPLOI_TG_URL_PATTERNS = [
    r'(https://www\.emploi\.tg/offre-emploi-togo/[^\s<>"\']*)',
    r'(https://www\.emploi\.tg/offre-emploi/[^\s<>"\']*)',
    r'(https://www\.emploi\.tg/node/\d+[^\s<>"\']*)'
]


# Configuration for Emploi.tg
EMPLOI_TG_CONFIG = SourceBaseConfig(
    name="Emploi.tg",
    base_url="https://www.emploi.tg",
    listing_url="https://www.emploi.tg/recherche-jobs-togo",
    source_type=SourceType.PRIVATE,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs="a[href*='offre']",
    max_pages=20,
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude="header, footer, .ads, .sidebar, .social-share",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=EMPLOI_TG_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=1.5,
    
    # Quality indicators
    expected_jobs_per_page=15,
    reliability_score=0.9,
    
    # Jina Reader specific parameters
    jina_params={
        "gather_all_links_at_the_end": "true",
        "remove_all_images": "true",
    }
)