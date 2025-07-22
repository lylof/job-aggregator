"""Configuration for YOP L-FRII job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to YOP L-FRII
YOP_LFRII_URL_PATTERNS = [
    r'(https://yop\.l-frii\.com/[^\s<>"\']*offres?-?d?-?emplois?[^\s<>"\']*)',
    r'(https://yop\.l-frii\.com/\d{4}/\d{2}/\d{2}/[^\s<>"\']*)'
]


# Configuration for YOP L-FRII
YOP_LFRII_CONFIG = SourceBaseConfig(
    name="YOP L-FRII",
    base_url="https://yop.l-frii.com",
    listing_url="https://yop.l-frii.com/offres-demplois/",
    source_type=SourceType.NGO,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs="h2.elementor-heading-title a",
    max_pages=83,  # Site has extensive pagination
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude="header, footer, .menu, .navigation",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=YOP_LFRII_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=2.0,  # Slower to be respectful
    custom_headers={
        "User-Agent": "Mozilla/5.0 (compatible; JinaJobScraper/1.0; +https://emploi.tg/bot)"
    },
    
    # Quality indicators
    expected_jobs_per_page=10,
    reliability_score=0.85,
    
    # Jina Reader specific parameters
    jina_params={
        "gather_all_links_at_the_end": "true",
        "remove_all_images": "true",
        "timeout": "45"  # Longer timeout for this site
    }
)