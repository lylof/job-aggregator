"""Configuration for LinkedIn Togo job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to LinkedIn Togo
LINKEDIN_TOGO_URL_PATTERNS = [
    r'(https://tg\.linkedin\.com/jobs/view/[^\s<>"\']*)',
    r'(https://www\.linkedin\.com/jobs/view/[^\s<>"\']*)'
]


# Configuration for LinkedIn Togo
LINKEDIN_TOGO_CONFIG = SourceBaseConfig(
    name="LinkedIn Togo",
    base_url="https://tg.linkedin.com",
    listing_url="https://tg.linkedin.com/jobs/search?location=Togo&geoId=103603395&f_TPR=r86400&currentJobId=&position=1&pageNum=0",
    source_type=SourceType.INTERNATIONAL,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs=".base-card__full-link",
    max_pages=10,
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude=".global-nav, .global-footer, .ad-banner",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=LINKEDIN_TOGO_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=2.0,  # LinkedIn has strict rate limiting
    requires_headers=True,
    custom_headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
    },
    
    # Quality indicators
    expected_jobs_per_page=25,
    reliability_score=0.9,
    
    # Jina Reader specific parameters
    jina_params={
        "gather_all_links_at_the_end": "true",
        "remove_all_images": "true",
        "timeout": "45",  # Longer timeout for LinkedIn
        "wait_for_selector": ".base-card__full-link"
    }
)