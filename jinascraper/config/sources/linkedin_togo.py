"""Configuration for LinkedIn Togo job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to LinkedIn Togo
LINKEDIN_TOGO_URL_PATTERNS = ['(https://tg\\.linkedin\\.com/jobs/view/[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
LINKEDIN_TOGO_BASE_CONFIG = SourceBaseConfig(
    name="LinkedIn Togo",
    base_url="https://tg.linkedin.com",
    listing_url="https://tg.linkedin.com/jobs/search?location=Togo&geoId=103603395&f_TPR=r86400&currentJobId=&position=1&pageNum=0",
    source_type=SourceType.INTERNATIONAL,
    url_patterns=LINKEDIN_TOGO_URL_PATTERNS,
    request_delay=2.0,
    expected_jobs_per_page=25,
    reliability_score=0.85
)


# Stage 1 configuration (URL exploration and discovery)
LINKEDIN_TOGO_STAGE1_CONFIG = SourceStage1Config(
    base=LINKEDIN_TOGO_BASE_CONFIG,
    css_selector_jobs='.base-card__full-link',  # Selon spécifications
    max_pages=20,
    jina_params={
        # Paramètres spécifiques LinkedIn Togo
        'target_selector': '.base-card__full-link',  # X-Target-Selector
        'timeout': '45',  # Timeout spécifique
        'css_selector_wait_for': '.base-card__full-link'  # Wait for selector
    }
)


# Stage 2 configuration (detailed content extraction and enrichment)
LINKEDIN_TOGO_STAGE2_CONFIG = SourceStage2Config(
    base=LINKEDIN_TOGO_BASE_CONFIG,
    enabled=True,
    css_selector_exclude='header, footer, .global-nav, .sidebar',
    jina_params={'css_selector_only': '.job-details, .job-view-layout, main', 'css_selector_excluding': 'header, footer, .global-nav, .sidebar, .ads', 'timeout': '45', 'with_generated_alt': 'true'},
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
LINKEDIN_TOGO_CONFIG = ConfigAdapter(
    LINKEDIN_TOGO_STAGE1_CONFIG,
    LINKEDIN_TOGO_STAGE2_CONFIG
)
