"""Configuration for ANPE Togo job source."""

from ..base_config import SourceBaseConfig, SourceType


# URL extraction patterns specific to ANPE Togo
ANPE_URL_PATTERNS = [
    r'(https://anpetogo\.org/job/[^\s<>"\']*)'
]


# Configuration for ANPE Togo
ANPE_TOGO_CONFIG = SourceBaseConfig(
    name="ANPE Togo",
    base_url="https://anpetogo.org",
    listing_url="https://anpetogo.org/espace-chercheur-d-emploi/nos-offres-demplois",
    source_type=SourceType.GOVERNMENT,
    
    # Stage 1 (Exploration) parameters
    css_selector_jobs=".jobsearch-joblisting-classic-wrap h2 a",
    max_pages=50,  # Government site with many offers
    
    # Stage 2 (Analysis) parameters
    css_selector_exclude="header, footer, .menu-principal, .sidebar",
    use_reader_lm=True,
    
    # URL extraction patterns
    url_patterns=ANPE_URL_PATTERNS,
    
    # Site-specific settings
    request_delay=1.0,
    
    # Quality indicators
    expected_jobs_per_page=15,
    reliability_score=0.95,  # High reliability for government source
    
    # Jina Reader specific parameters
    jina_params={
        "css_selector_only": ".jobsearch-joblisting-classic-wrap",
        "css_selector_wait_for": ".jobsearch-joblisting-classic-wrap",
    }
)