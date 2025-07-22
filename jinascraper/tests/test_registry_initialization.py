"""Test the initialization of the source registry."""

import pytest
from jinascraper.config import SourceRegistry, initialize_registry


def test_registry_initialization():
    """Test that the registry is initialized with the expected sources."""
    # Clear registry
    SourceRegistry._sources = {}
    
    # Initialize registry
    initialize_registry()
    
    # Check that ANPE Togo is registered
    assert "anpetogo" in SourceRegistry._sources
    
    # Check ANPE Togo configuration
    anpe_config = SourceRegistry.get_source("anpetogo")
    assert anpe_config is not None
    assert anpe_config.name == "ANPE Togo"
    assert anpe_config.base_url == "https://anpetogo.org"
    
    # Check that we can get active sources
    active_sources = SourceRegistry.get_active_sources()
    assert "anpetogo" in active_sources
    
    # Check that we can get sources by type
    from jinascraper.config import SourceType
    government_sources = SourceRegistry.get_sources_by_type(SourceType.GOVERNMENT)
    assert "anpetogo" in government_sources