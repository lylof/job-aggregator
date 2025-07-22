"""Tests for URL cleaners."""

import pytest
from jinascraper.services.url_cleaners.anpetogo_cleaner import (
    clean_anpe_urls,
    clean_anpe_url,
    is_valid_anpe_url
)
from jinascraper.services.url_cleaner import (
    clean_url,
    clean_generic_urls,
    clean_urls_by_source
)


def test_clean_url():
    """Test clean_url function."""
    # Test removing problematic characters
    assert clean_url("https://example.com/job/123.") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123,") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123;") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123:") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123!") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123?") == "https://example.com/job/123"
    assert clean_url("https://example.com/job/123)") == "https://example.com/job/123"
    
    # Test normal URL
    assert clean_url("https://example.com/job/123") == "https://example.com/job/123"


def test_clean_anpe_url():
    """Test clean_anpe_url function."""
    # Test removing problematic characters
    assert clean_anpe_url("https://anpetogo.org/job/123.") == "https://anpetogo.org/job/123/"
    
    # Test adding trailing slash
    assert clean_anpe_url("https://anpetogo.org/job/123") == "https://anpetogo.org/job/123/"
    
    # Test URL with trailing slash
    assert clean_anpe_url("https://anpetogo.org/job/123/") == "https://anpetogo.org/job/123/"


def test_is_valid_anpe_url():
    """Test is_valid_anpe_url function."""
    # Test valid URLs
    assert is_valid_anpe_url("https://anpetogo.org/job/123/") is True
    assert is_valid_anpe_url("https://anpetogo.org/job/assistant-administratif/") is True
    
    # Test invalid URLs
    assert is_valid_anpe_url("https://anpetogo.org/") is False
    assert is_valid_anpe_url("https://anpetogo.org/job/") is False
    assert is_valid_anpe_url("https://example.com/job/123/") is False
    assert is_valid_anpe_url("not a url") is False


def test_clean_anpe_urls():
    """Test clean_anpe_urls function."""
    urls = [
        "https://anpetogo.org/job/123",
        "https://anpetogo.org/job/456/",
        "https://anpetogo.org/job/123.",  # Duplicate after cleaning
        "https://anpetogo.org/",  # Invalid
        "https://example.com/job/123/"  # Invalid
    ]
    
    cleaned_urls = clean_anpe_urls(urls)
    
    assert len(cleaned_urls) == 2
    assert "https://anpetogo.org/job/123/" in cleaned_urls
    assert "https://anpetogo.org/job/456/" in cleaned_urls


def test_clean_generic_urls():
    """Test clean_generic_urls function."""
    urls = [
        "https://example.com/job/123",
        "https://example.com/job/456/",
        "https://example.com/job/123.",  # Duplicate after cleaning
        "not a url"  # Invalid
    ]
    
    cleaned_urls = clean_generic_urls(urls)
    
    assert len(cleaned_urls) == 2
    assert "https://example.com/job/123" in cleaned_urls
    assert "https://example.com/job/456/" in cleaned_urls


def test_clean_urls_by_source():
    """Test clean_urls_by_source function."""
    urls = [
        "https://anpetogo.org/job/123",
        "https://anpetogo.org/job/456/",
        "https://anpetogo.org/job/123.",  # Duplicate after cleaning
        "https://anpetogo.org/",  # Invalid
        "https://example.com/job/123/"  # Invalid for ANPE
    ]
    
    # Test with ANPE source
    anpe_urls = clean_urls_by_source(urls, "anpetogo")
    assert len(anpe_urls) == 2
    assert "https://anpetogo.org/job/123/" in anpe_urls
    assert "https://anpetogo.org/job/456/" in anpe_urls
    
    # Test with unknown source (should use generic cleaner)
    generic_urls = clean_urls_by_source(urls, "unknown_source")
    assert len(generic_urls) >= 3  # Generic cleaner is less strict