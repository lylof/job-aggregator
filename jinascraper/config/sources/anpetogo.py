"""Configuration for ANPE Togo job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to ANPE Togo
ANPETOGO_URL_PATTERNS = ['(https://anpetogo\\.org/job/[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
ANPETOGO_BASE_CONFIG = SourceBaseConfig(
    name="ANPE Togo",
    base_url="https://anpetogo.org",
    listing_url="https://anpetogo.org/espace-chercheur-d-emploi/nos-offres-demplois",
    source_type=SourceType.GOVERNMENT,
    url_patterns=ANPETOGO_URL_PATTERNS,
    request_delay=1.0,
    expected_jobs_per_page=15,
    reliability_score=0.95
)


# Stage 1 configuration (URL exploration and discovery)
ANPETOGO_STAGE1_CONFIG = SourceStage1Config(
    base=ANPETOGO_BASE_CONFIG,
    css_selector_jobs='h2 > a',  # Simplifié selon X-Target-Selector
    max_pages=50,
    jina_params={
        # Paramètres spécifiques ANPE
        'remove_selector': 'header#careerfy-header, div.jobsearch-banner-search, div.jobsearch-column-3.jobsearch-typo-wrap, footer#careerfy-footer',  # X-Remove-Selector
        'target_selector': 'h2 > a'  # X-Target-Selector
    }
)


# Stage 2 configuration (detailed content extraction and enrichment)
ANPETOGO_STAGE2_CONFIG = SourceStage2Config(
    base=ANPETOGO_BASE_CONFIG,
    enabled=True,
    css_selector_exclude='header, footer, .menu-principal, .sidebar',
    jina_params={'css_selector_only': '.job-details, .offre-content, .job-description, main, .content-area', 'css_selector_excluding': 'header, footer, .menu-principal, .sidebar, .navigation, .breadcrumb, .admin-bar', 'timeout': '60', 'with_generated_alt': 'true'},
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
ANPETOGO_CONFIG = ConfigAdapter(
    ANPETOGO_STAGE1_CONFIG,
    ANPETOGO_STAGE2_CONFIG
)
