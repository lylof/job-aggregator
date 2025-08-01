"""Configuration for EmploiTogo.info job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to EmploiTogo.info
EMPLOITOGO_INFO_URL_PATTERNS = ['(https://www\\.emploitogo\\.info/[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
EMPLOITOGO_INFO_BASE_CONFIG = SourceBaseConfig(
    name="EmploiTogo.info",
    base_url="https://emploitogo.info",
    listing_url="https://www.emploitogo.info/emploitogo/",
    source_type=SourceType.PRIVATE,
    url_patterns=EMPLOITOGO_INFO_URL_PATTERNS,
    request_delay=1.5,
    expected_jobs_per_page=18,
    reliability_score=0.8
)


# Stage 1 configuration (URL exploration and discovery)
EMPLOITOGO_INFO_STAGE1_CONFIG = SourceStage1Config(
    base=EMPLOITOGO_INFO_BASE_CONFIG,
    css_selector_jobs='h3 > a',  # Simplifié selon X-Target-Selector
    max_pages=30,
    jina_params={
        # Paramètre spécifique emploitogo.info
        'target_selector': 'h3 > a'  # X-Target-Selector
    }
)


# Stage 2 configuration (detailed content extraction and enrichment)
EMPLOITOGO_INFO_STAGE2_CONFIG = SourceStage2Config(
    base=EMPLOITOGO_INFO_BASE_CONFIG,
    enabled=True,
    css_selector_exclude='header, footer, .sidebar, .ads',
    jina_params={'css_selector_only': '.job-details, .offre-content, main', 'css_selector_excluding': 'header, footer, .sidebar, .ads', 'timeout': '50', 'with_generated_alt': 'true'},
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
EMPLOITOGO_INFO_CONFIG = ConfigAdapter(
    EMPLOITOGO_INFO_STAGE1_CONFIG,
    EMPLOITOGO_INFO_STAGE2_CONFIG
)
