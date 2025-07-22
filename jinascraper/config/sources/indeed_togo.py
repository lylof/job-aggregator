"""Configuration for Indeed Togo job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to Indeed Togo
INDEED_TOGO_URL_PATTERNS = [
    r'(https://fr\.indeed\.com/voir-emploi\?jk=[^\s<>"\'&]*)',
    r'(https://fr\.indeed\.com/viewjob\?jk=[^\s<>"\'&]*)'
]


# Configuration for Indeed Togo
INDEED_TOGO_CONFIG = SourceBaseConfig(
    name="Indeed Togo",
    base_url="https://fr.indeed.com",
    listing_url="https://fr.indeed.com/q-togo,-lomé-emplois.html",
    source_type=SourceType.INTERNATIONAL,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs=".job_seen_beacon, .slider_container .slider_item",
    max_pages=20,
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude="#searchform, .np-footer, .jobsearch-SerpJobCard-footer",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=INDEED_TOGO_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=1.5,
    requires_headers=True,
    custom_headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9"
    },
    
    # Quality indicators
    expected_jobs_per_page=15,
    reliability_score=0.85,
    disabled=True,  # Temporarily disabled - strict anti-bot protections
    
    # Jina Reader specific parameters
    jina_params={
        "gather_all_links_at_the_end": "true",
        "remove_all_images": "true",
        "timeout": "45",  # Longer timeout for Indeed
        "wait_for_selector": ".job_seen_beacon"
    }
)