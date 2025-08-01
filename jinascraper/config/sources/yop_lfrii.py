"""Configuration for YOP L'Frii job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to YOP L'Frii
YOP_LFRII_URL_PATTERNS = ['(https://yop\\.l-frii\\.com/emploi/[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
YOP_LFRII_BASE_CONFIG = SourceBaseConfig(
    name="YOP L'Frii",
    base_url="https://yop.l-frii.com",
    listing_url="https://yop.l-frii.com/offres-demplois/",
    source_type=SourceType.PRIVATE,
    url_patterns=YOP_LFRII_URL_PATTERNS,
    request_delay=1.5,
    expected_jobs_per_page=12,
    reliability_score=0.75
)


# Stage 1 configuration (URL exploration and discovery)
YOP_LFRII_STAGE1_CONFIG = SourceStage1Config(
    base=YOP_LFRII_BASE_CONFIG,
    css_selector_jobs='h2.elementor-heading-title.elementor-size-default a',  # Selon X-Target-Selector
    max_pages=25,
    jina_params={
        # Paramètre spécifique YOP L'Frii
        'target_selector': 'h2.elementor-heading-title.elementor-size-default a'  # X-Target-Selector
    }
)


# Stage 2 configuration (detailed content extraction and enrichment)
YOP_LFRII_STAGE2_CONFIG = SourceStage2Config(
    base=YOP_LFRII_BASE_CONFIG,
    enabled=True,
    css_selector_exclude='header, footer, .sidebar, .pub',
    jina_params={'css_selector_only': '.job-details, .emploi-content, main', 'css_selector_excluding': 'header, footer, .sidebar, .pub', 'timeout': '45', 'with_generated_alt': 'true'},
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
YOP_LFRII_CONFIG = ConfigAdapter(
    YOP_LFRII_STAGE1_CONFIG,
    YOP_LFRII_STAGE2_CONFIG
)
