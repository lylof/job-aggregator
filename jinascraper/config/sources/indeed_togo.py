"""Configuration for Indeed Togo job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to Indeed Togo
INDEED_TOGO_URL_PATTERNS = ['(https://tg\\.indeed\\.com/viewjob[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
INDEED_TOGO_BASE_CONFIG = SourceBaseConfig(
    name="Indeed Togo",
    base_url="https://tg.indeed.com",
    listing_url="https://tg.indeed.com/jobs",
    source_type=SourceType.INTERNATIONAL,
    url_patterns=INDEED_TOGO_URL_PATTERNS,
    request_delay=2.0,
    expected_jobs_per_page=15,
    reliability_score=0.85
)


# Stage 1 configuration (URL exploration and discovery)
INDEED_TOGO_STAGE1_CONFIG = SourceStage1Config(
    base=INDEED_TOGO_BASE_CONFIG,
    css_selector_jobs='.jobsearch-SerpJobCard h2 a, .job_seen_beacon a',
    max_pages=50,
    jina_params={'css_selector_only': '.jobsearch-SerpJobCard, .job_seen_beacon', 'timeout': '35'}
)


# Stage 2 configuration (detailed content extraction and enrichment)
INDEED_TOGO_STAGE2_CONFIG = SourceStage2Config(
    base=INDEED_TOGO_BASE_CONFIG,
    enabled=True,
    css_selector_exclude='header, footer, .leftrail, .rightrail',
    jina_params={'css_selector_only': '.jobsearch-JobComponent, .jobsearch-JobMetadataHeader', 'css_selector_excluding': 'header, footer, .leftrail, .rightrail, .ads', 'timeout': '45', 'with_generated_alt': 'true'},
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
INDEED_TOGO_CONFIG = ConfigAdapter(
    INDEED_TOGO_STAGE1_CONFIG,
    INDEED_TOGO_STAGE2_CONFIG
)
