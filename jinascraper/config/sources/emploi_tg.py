"""Configuration for Emploi.tg job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to Emploi.tg
EMPLOI_TG_URL_PATTERNS = ['(https://www\\.emploi\\.tg/offre-emploi-togo/[^\\s<>"\\\']*)']


# Base source configuration (stage-agnostic)
EMPLOI_TG_BASE_CONFIG = SourceBaseConfig(
    name="Emploi.tg",
    base_url="https://www.emploi.tg",
    listing_url="https://www.emploi.tg/recherche-jobs-togo",
    source_type=SourceType.GOVERNMENT,
    url_patterns=EMPLOI_TG_URL_PATTERNS,
    request_delay=1.0,
    expected_jobs_per_page=20,
    reliability_score=0.9
)


# Stage 1 configuration (URL exploration and discovery)
EMPLOI_TG_STAGE1_CONFIG = SourceStage1Config(
    base=EMPLOI_TG_BASE_CONFIG,
    css_selector_jobs='h3 > a',  # Simplifié selon X-Target-Selector
    max_pages=100,
    jina_params={
        # Paramètre spécifique emploi.tg
        'target_selector': 'h3 > a'  # X-Target-Selector
    }
)


# Stage 2 configuration (detailed content extraction and enrichment) - Nouvelle stratégie robuste
EMPLOI_TG_STAGE2_CONFIG = SourceStage2Config(
    base=EMPLOI_TG_BASE_CONFIG,
    enabled=True,
    jina_params={
        # Sélecteurs CSS spécifiques pour emploi.tg - Nouvelle stratégie
        'target_selector': 'div.card.card-block.card-block-summary,div.card.card-block.mt-3,div.block-links',
        'remove_selector': 'em.text-md, div.block-links .sponsor, div.card-block-summary .unwanted-class',
        
        # Paramètres de base hérités de la nouvelle configuration
        'engine': 'browser',
        'no_cache': 'true',
        'return_format': 'markdown',
        'timeout': '30',
        'with_generated_alt': 'true'
    },
    gemini_config={'model': 'gemini-1.5-flash', 'temperature': 0.1, 'max_tokens': 2048}
)


# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
EMPLOI_TG_CONFIG = ConfigAdapter(
    EMPLOI_TG_STAGE1_CONFIG,
    EMPLOI_TG_STAGE2_CONFIG
)
