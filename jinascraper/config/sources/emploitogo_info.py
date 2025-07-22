"""Configuration for EmploiTogo.info job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to EmploiTogo.info
EMPLOITOGO_INFO_URL_PATTERNS = [
    r'(https://www\.emploitogo\.info/\d{4}/\d{2}/[^\s<>"\']*\.html)',
    r'(https://www\.emploitogo\.info/[^\s<>"\']*-emploi[^\s<>"\']*\.html)'
]


# Configuration for EmploiTogo.info
EMPLOITOGO_INFO_CONFIG = SourceBaseConfig(
    name="EmploiTogo.info",
    base_url="https://www.emploitogo.info",
    listing_url="https://www.emploitogo.info/emploitogo/",
    source_type=SourceType.PRIVATE,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs="h3.job-title a, h3.entry-title a",
    max_pages=15,
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude="header, footer, .pub, .advertisement",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=EMPLOITOGO_INFO_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=1.0,
    
    # Quality indicators
    expected_jobs_per_page=12,
    reliability_score=0.8,
    
    # Jina Reader specific parameters
    jina_params={
        "gather_all_links_at_the_end": "true",
        "remove_all_images": "true",
    }
)