#!/usr/bin/env python3
"""
Script to migrate all source configurations to new layered architecture.
This will update all source config files to use the new format.
"""

import sys
from pathlib import Path

# Add jinascraper to path
sys.path.insert(0, str(Path(__file__).parent))

from config.base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, JinaReaderTechnicalConfig,
    DEFAULT_TECHNICAL_CONFIG, SourceType
)


def generate_new_source_config(source_name: str, old_config_dict: dict) -> str:
    """
    Generate new source configuration file content.
    
    Args:
        source_name: Name of the source (e.g., "anpetogo")
        old_config_dict: Dictionary with old configuration values
        
    Returns:
        String content for new configuration file
    """
    
    # Extract values from old config
    name = old_config_dict.get("name", "")
    base_url = old_config_dict.get("base_url", "")
    listing_url = old_config_dict.get("listing_url", "")
    source_type = old_config_dict.get("source_type", "private")
    url_patterns = old_config_dict.get("url_patterns", [])
    
    # Stage 1 specific
    css_selector_jobs = old_config_dict.get("css_selector_jobs")
    max_pages = old_config_dict.get("max_pages", 10)
    jina_params = old_config_dict.get("jina_params", {})
    
    # Stage 2 specific
    css_selector_exclude = old_config_dict.get("css_selector_exclude")
    stage2_params = old_config_dict.get("stage2_params", {})
    
    # Quality indicators
    expected_jobs_per_page = old_config_dict.get("expected_jobs_per_page", 20)
    reliability_score = old_config_dict.get("reliability_score", 0.8)
    request_delay = old_config_dict.get("request_delay", 1.0)
    
    # Generate file content
    content = f'''"""Configuration for {name} job source - New Layered Architecture."""

from ..base_config import (
    SourceBaseConfig, SourceStage1Config, SourceStage2Config,
    Stage1JinaConfig, Stage2JinaConfig, DEFAULT_TECHNICAL_CONFIG,
    SourceType
)


# URL extraction patterns specific to {name}
{source_name.upper()}_URL_PATTERNS = {url_patterns!r}


# Base source configuration (stage-agnostic)
{source_name.upper()}_BASE_CONFIG = SourceBaseConfig(
    name="{name}",
    base_url="{base_url}",
    listing_url="{listing_url}",
    source_type=SourceType.{source_type.upper()},
    url_patterns={source_name.upper()}_URL_PATTERNS,
    request_delay={request_delay},
    expected_jobs_per_page={expected_jobs_per_page},
    reliability_score={reliability_score}
)


# Stage 1 configuration (URL exploration and discovery)
{source_name.upper()}_STAGE1_CONFIG = SourceStage1Config(
    base={source_name.upper()}_BASE_CONFIG,
    css_selector_jobs={css_selector_jobs!r},
    max_pages={max_pages},
    jina_params={jina_params!r}
)
'''

    # Add Stage 2 configuration if it exists
    if stage2_params:
        stage2_jina_params = stage2_params.get("jina_params", {})
        gemini_config = stage2_params.get("gemini_config", {
            "model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_tokens": 2048
        })
        enabled = stage2_params.get("enabled", False)
        
        content += f'''

# Stage 2 configuration (detailed content extraction and enrichment)
{source_name.upper()}_STAGE2_CONFIG = SourceStage2Config(
    base={source_name.upper()}_BASE_CONFIG,
    enabled={enabled},
    css_selector_exclude={css_selector_exclude!r},
    jina_params={stage2_jina_params!r},
    gemini_config={gemini_config!r}
)
'''
    else:
        content += f'''

# Stage 2 configuration (disabled by default)
{source_name.upper()}_STAGE2_CONFIG = SourceStage2Config(
    base={source_name.upper()}_BASE_CONFIG,
    enabled=False,
    css_selector_exclude={css_selector_exclude!r}
)
'''

    # Add backward compatibility
    content += f'''

# Backward compatibility - provides old-style interface
from ..migration_helper import ConfigAdapter
{source_name.upper()}_CONFIG = ConfigAdapter(
    {source_name.upper()}_STAGE1_CONFIG,
    {source_name.upper()}_STAGE2_CONFIG
)
'''

    return content


def migrate_anpetogo():
    """Migrate ANPE Togo configuration."""
    old_config = {
        "name": "ANPE Togo",
        "base_url": "https://anpetogo.org",
        "listing_url": "https://anpetogo.org/espace-chercheur-d-emploi/nos-offres-demplois",
        "source_type": "government",
        "css_selector_jobs": ".jobsearch-joblisting-classic-wrap h2 a",
        "max_pages": 50,
        "css_selector_exclude": "header, footer, .menu-principal, .sidebar",
        "url_patterns": [r'(https://anpetogo\.org/job/[^\s<>"\']*)', ],
        "request_delay": 1.0,
        "expected_jobs_per_page": 15,
        "reliability_score": 0.95,
        "jina_params": {
            "css_selector_only": ".jobsearch-joblisting-classic-wrap",
            "css_selector_wait_for": ".jobsearch-joblisting-classic-wrap",
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".job-details, .offre-content, .job-description, main, .content-area",
                "css_selector_excluding": "header, footer, .menu-principal, .sidebar, .navigation, .breadcrumb, .admin-bar",
                "use_reader_lm_v2": "true",
                "timeout": "60",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("anpetogo", old_config)
    
    with open("config/sources/anpetogo.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated ANPE Togo configuration")


def migrate_emploi_tg():
    """Migrate Emploi.tg configuration."""
    old_config = {
        "name": "Emploi.tg",
        "base_url": "https://emploi.tg",
        "listing_url": "https://emploi.tg/offres-emploi",
        "source_type": "government",
        "css_selector_jobs": ".job-item h3 a, .job-listing-item h2 a",
        "max_pages": 100,
        "css_selector_exclude": "header, footer, .sidebar, .ads",
        "url_patterns": [r'(https://emploi\.tg/offre-emploi/[^\s<>"\']*)', ],
        "request_delay": 1.0,
        "expected_jobs_per_page": 20,
        "reliability_score": 0.90,
        "jina_params": {
            "css_selector_only": ".job-item, .job-listing-item",
            "css_selector_wait_for": ".job-item",
            "timeout": "45",
            "gather_all_links_at_the_end": "true",
            "remove_all_images": "true"
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".job-details, .offre-content, .job-description, main, .content-area",
                "css_selector_excluding": "header, footer, .sidebar, .ads, .navigation, .breadcrumb",
                "use_reader_lm_v2": "true",
                "timeout": "60",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("emploi_tg", old_config)
    
    with open("config/sources/emploi_tg.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated Emploi.tg configuration")


def migrate_linkedin_togo():
    """Migrate LinkedIn Togo configuration."""
    old_config = {
        "name": "LinkedIn Togo",
        "base_url": "https://www.linkedin.com",
        "listing_url": "https://www.linkedin.com/jobs/search/?location=Togo",
        "source_type": "international",
        "css_selector_jobs": ".job-search-card h3 a, .jobs-search__results-list .job-search-card a",
        "max_pages": 20,
        "css_selector_exclude": "header, footer, .global-nav, .sidebar",
        "url_patterns": [r'(https://www\.linkedin\.com/jobs/view/\d+[^\s<>"\']*)', ],
        "request_delay": 2.0,
        "expected_jobs_per_page": 25,
        "reliability_score": 0.85,
        "jina_params": {
            "css_selector_only": ".job-search-card, .jobs-search__results-list",
            "timeout": "30",
            "gather_all_links_at_the_end": "true"
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".job-details, .job-view-layout, main",
                "css_selector_excluding": "header, footer, .global-nav, .sidebar, .ads",
                "use_reader_lm_v2": "true",
                "timeout": "45",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("linkedin_togo", old_config)
    
    with open("config/sources/linkedin_togo.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated LinkedIn Togo configuration")


def migrate_emploitogo_info():
    """Migrate EmploiTogo.info configuration."""
    old_config = {
        "name": "EmploiTogo.info",
        "base_url": "https://emploitogo.info",
        "listing_url": "https://emploitogo.info/offres-emploi",
        "source_type": "private",
        "css_selector_jobs": ".job-item h3 a, .job-listing h2 a",
        "max_pages": 30,
        "css_selector_exclude": "header, footer, .sidebar, .ads",
        "url_patterns": [r'(https://emploitogo\.info/offre/[^\s<>"\']*)', ],
        "request_delay": 1.5,
        "expected_jobs_per_page": 18,
        "reliability_score": 0.80,
        "jina_params": {
            "css_selector_only": ".job-item, .job-listing",
            "timeout": "40"
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".job-details, .offre-content, main",
                "css_selector_excluding": "header, footer, .sidebar, .ads",
                "use_reader_lm_v2": "true",
                "timeout": "50",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("emploitogo_info", old_config)
    
    with open("config/sources/emploitogo_info.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated EmploiTogo.info configuration")


def migrate_indeed_togo():
    """Migrate Indeed Togo configuration."""
    old_config = {
        "name": "Indeed Togo",
        "base_url": "https://tg.indeed.com",
        "listing_url": "https://tg.indeed.com/jobs",
        "source_type": "international",
        "css_selector_jobs": ".jobsearch-SerpJobCard h2 a, .job_seen_beacon a",
        "max_pages": 50,
        "css_selector_exclude": "header, footer, .leftrail, .rightrail",
        "url_patterns": [r'(https://tg\.indeed\.com/viewjob[^\s<>"\']*)', ],
        "request_delay": 2.0,
        "expected_jobs_per_page": 15,
        "reliability_score": 0.85,
        "jina_params": {
            "css_selector_only": ".jobsearch-SerpJobCard, .job_seen_beacon",
            "timeout": "35"
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".jobsearch-JobComponent, .jobsearch-JobMetadataHeader",
                "css_selector_excluding": "header, footer, .leftrail, .rightrail, .ads",
                "use_reader_lm_v2": "true",
                "timeout": "45",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("indeed_togo", old_config)
    
    with open("config/sources/indeed_togo.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated Indeed Togo configuration")


def migrate_yop_lfrii():
    """Migrate YOP L'Frii configuration."""
    old_config = {
        "name": "YOP L'Frii",
        "base_url": "https://yop.l-frii.com",
        "listing_url": "https://yop.l-frii.com/emploi",
        "source_type": "private",
        "css_selector_jobs": ".job-item h3 a, .emploi-item h2 a",
        "max_pages": 25,
        "css_selector_exclude": "header, footer, .sidebar, .pub",
        "url_patterns": [r'(https://yop\.l-frii\.com/emploi/[^\s<>"\']*)', ],
        "request_delay": 1.5,
        "expected_jobs_per_page": 12,
        "reliability_score": 0.75,
        "jina_params": {
            "css_selector_only": ".job-item, .emploi-item",
            "timeout": "35"
        },
        "stage2_params": {
            "jina_params": {
                "css_selector_only": ".job-details, .emploi-content, main",
                "css_selector_excluding": "header, footer, .sidebar, .pub",
                "use_reader_lm_v2": "true",
                "timeout": "45",
                "with_generated_alt": "true"
            },
            "gemini_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048
            },
            "enabled": True
        }
    }
    
    content = generate_new_source_config("yop_lfrii", old_config)
    
    with open("config/sources/yop_lfrii.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Migrated YOP L'Frii configuration")


def main():
    """Run all migrations."""
    print("🔄 Migrating source configurations to new layered architecture...\n")
    
    try:
        migrate_anpetogo()
        migrate_emploi_tg()
        migrate_linkedin_togo()
        migrate_emploitogo_info()
        migrate_indeed_togo()
        migrate_yop_lfrii()
        
        print("\n🎉 All source configurations migrated successfully!")
        print("\n📋 New structure for each source:")
        print("  • {SOURCE}_BASE_CONFIG: Common source information")
        print("  • {SOURCE}_STAGE1_CONFIG: Stage 1 specific configuration")
        print("  • {SOURCE}_STAGE2_CONFIG: Stage 2 specific configuration")
        print("  • {SOURCE}_CONFIG: Backward compatibility adapter")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()