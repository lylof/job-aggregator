"""URL cleaner for YOP L-FRII job source."""

import re
from urllib.parse import urlparse
from ...utils.type_helpers import List


def clean_yop_lfrii_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to YOP L-FRII.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    cleaned_urls = []
    
    for url in urls:
        # Basic cleaning
        url = clean_yop_lfrii_url(url)
        
        # Validate URL
        if is_valid_yop_lfrii_url(url) and url not in cleaned_urls:
            cleaned_urls.append(url)
    
    return cleaned_urls


def clean_yop_lfrii_url(url: str) -> str:
    """
    Clean a YOP L-FRII URL specifically.
    
    Args:
        url: YOP L-FRII URL to clean
        
    Returns:
        Cleaned YOP L-FRII URL
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
    
    # Ensure URL doesn't end with a trailing slash if it's a specific job post
    if re.search(r'/\d{4}/\d{2}/\d{2}/[^/]+/$', url):
        url = url.rstrip('/')
    
    return url


def is_valid_yop_lfrii_url(url: str) -> bool:
    """
    Validate that an URL is a valid YOP L-FRII job offer URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is a valid YOP L-FRII job offer URL
    """
    try:
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc != "yop.l-frii.com":
            return False
        
        # Check path patterns
        valid_patterns = [
            r'^/\d{4}/\d{2}/\d{2}/[^/]+/?$',  # Date-based post
            r'^/offres?-?d?-?emplois?/[^/]+/?$',  # Job offer section
            r'^/[^/]*offres?-?d?-?emplois?[^/]*/?$'  # Contains "offre-emploi" or variants
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, parsed.path):
                return True
        
        return False
        
    except Exception:
        return False