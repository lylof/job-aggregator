"""URL cleaner for EmploiTogo.info job source."""

import re
from urllib.parse import urlparse
from typing import List


def clean_emploitogo_info_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to EmploiTogo.info.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    cleaned_urls = []
    
    for url in urls:
        # Basic cleaning
        url = clean_emploitogo_info_url(url)
        
        # Validate URL
        if is_valid_emploitogo_info_url(url) and url not in cleaned_urls:
            cleaned_urls.append(url)
    
    return cleaned_urls


def clean_emploitogo_info_url(url: str) -> str:
    """
    Clean an EmploiTogo.info URL specifically.
    
    Args:
        url: EmploiTogo.info URL to clean
        
    Returns:
        Cleaned EmploiTogo.info URL
    """
    # Remove problematic characters
    url = re.sub(r'[.,;:!?)\\]$', '', url)
    
    # Remove trailing parenthesis
    url = url.rstrip(')')
    
    # Remove URL fragments
    if '#' in url:
        url = url.split('#')[0]
    
    # Remove query parameters
    if '?' in url:
        url = url.split('?')[0]
    
    return url


def is_valid_emploitogo_info_url(url: str) -> bool:
    """
    Validate that an URL is a valid EmploiTogo.info job offer URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is a valid EmploiTogo.info job offer URL
    """
    try:
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc != "www.emploitogo.info":
            return False
        
        # FIXED PATTERNS - Based on validation report analysis
        # Real URLs follow pattern: /emploitogo/offre-demploi-togo-charge-de-communication/
        valid_patterns = [
            r'^/emploitogo/[^/]+/?$'   # Main pattern for job URLs under /emploitogo/
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, parsed.path):
                return True
        
        return False
        
    except Exception:
        return False