"""Tests for the configuration architecture."""

import pytest
from jinascraper.config import (
    SourceBaseConfig,
    JinaReaderBaseConfig,
    SourceType,
    JINA_BASE_CONFIG,
    SourceRegistry
)
from jinascraper.config.sources.anpetogo import ANPE_TOGO_CONFIG


def test_jina_reader_base_config():
    """Test JinaReaderBaseConfig."""
    config = JinaReaderBaseConfig(timeout=60, retry_attempts=5)
    
    assert config.timeout == 60
    assert config.retry_attempts == 5
    assert config.with_images is False
    assert config.with_links is True
    
    # Test to_dict method
    config_dict = config.to_dict()
    assert config_dict["timeout"] == 60
    assert config_dict["retry_attempts"] == 5
    assert config_dict["with_images"] == "false"
    assert config_dict["with_links"] == "true"


def test_source_base_config():
    """Test SourceBaseConfig."""
    config = SourceBaseConfig(
        name="Test Source",
        base_url="https://test.com",
        listing_url="https://test.com/jobs",
        source_type=SourceType.PRIVATE,
        jina_params={"timeout": 60}
    )
    
    assert config.name == "Test Source"
    assert config.base_url == "https://test.com"
    assert config.listing_url == "https://test.com/jobs"
    assert config.source_type == SourceType.PRIVATE
    assert config.jina_params == {"timeout": 60}
    
    # Test validate method
    assert config.validate() is True
    
    # Test get_jina_params method
    base_config = JinaReaderBaseConfig(timeout=30, retry_attempts=3)
    merged_params = config.get_jina_params(base_config)
    
    assert merged_params["timeout"] == 60  # Overridden by source config
    assert merged_params["retry_attempts"] == 3  # From base config


def test_source_registry():
    """Test SourceRegistry."""
    # Clear registry
    SourceRegistry._sources = {}
    
    # Register a source
    config = SourceBaseConfig(
        name="Test Source",
        base_url="https://test.com",
        listing_url="https://test.com/jobs",
        source_type=SourceType.PRIVATE
    )
    
    SourceRegistry.register_source("test_source", config)
    
    # Test get_source
    retrieved_config = SourceRegistry.get_source("test_source")
    assert retrieved_config is config
    
    # Test get_all_sources
    all_sources = SourceRegistry.get_all_sources()
    assert len(all_sources) == 1
    assert "test_source" in all_sources
    
    # Test get_active_sources
    config.disabled = False
    active_sources = SourceRegistry.get_active_sources()
    assert len(active_sources) == 1
    
    config.disabled = True
    active_sources = SourceRegistry.get_active_sources()
    assert len(active_sources) == 0
    
    # Test get_sources_by_type
    config.disabled = False
    private_sources = SourceRegistry.get_sources_by_type(SourceType.PRIVATE)
    assert len(private_sources) == 1
    
    government_sources = SourceRegistry.get_sources_by_type(SourceType.GOVERNMENT)
    assert len(government_sources) == 0


def test_anpe_togo_config():
    """Test ANPE Togo configuration."""
    config = ANPE_TOGO_CONFIG
    
    assert config.name == "ANPE Togo"
    assert config.base_url == "https://anpetogo.org"
    assert config.source_type == SourceType.GOVERNMENT
    assert config.reliability_score == 0.95
    
    # Test URL patterns
    assert len(config.url_patterns) == 1
    assert config.url_patterns[0] == r'(https://anpetogo\.org/job/[^\s<>"\']*)'
    
    # Test Jina parameters
    assert "css_selector_only" in config.jina_params
    assert config.jina_params["css_selector_only"] == ".jobsearch-joblisting-classic-wrap"
    
    # Test merged parameters
    merged_params = config.get_jina_params(JINA_BASE_CONFIG)
    assert merged_params["css_selector_only"] == ".jobsearch-joblisting-classic-wrap"
    assert merged_params["timeout"] == 30  # From base config