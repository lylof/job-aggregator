"""URL cleaner for Indeed Togo job source."""

import re
from urllib.parse import urlparse, parse_qs
from ...utils.type_helpers import List


def clean_indeed_togo_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to Indeed Togo.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    cleaned_urls = []
    
    for url in urls:
        # Basic cleaning
        url = clean_indeed_togo_url(url)
        
        # Validate URL
        if is_valid_indeed_togo_url(url) and url not in cleaned_urls:
            cleaned_urls.append(url)
    
    return cleaned_urls


def clean_indeed_togo_url(url: str) -> str:
    """
    Clean an Indeed Togo URL specifically.
    
    Args:
        url: Indeed Togo URL to clean
        
    Returns:
        Cleaned Indeed Togo URL
    """
    # Remove problematic characters
    url = re.sub(r'[.,;:!?)\\]$', '', url)
    
    # Remove trailing parenthesis
    url = url.rstrip(')')
    
    # Parse URL to handle query parameters
    parsed = urlparse(url)
    
    # Keep only essential query parameters
    if parsed.query:
        query_params = parse_qs(parsed.query)
        essential_params = {}
        
        # Keep only job ID (jk) parameter
        if 'jk' in query_params:
            essential_params['jk'] = query_params['jk'][0]
        
        # Reconstruct URL with only essential parameters
        if essential_params:
            query_string = '&'.join([f"{k}={v}" for k, v in essential_params.items()])
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query_string}"
        else:
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    return url


def is_valid_indeed_togo_url(url: str) -> bool:
    """
    Validate that an URL is a valid Indeed Togo job offer URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is a valid Indeed Togo job offer URL
    """
    try:
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc != "fr.indeed.com":
            return False
        
        # Check path pattern for job view
        valid_paths = ['/voir-emploi', '/viewjob']
        if parsed.path not in valid_paths:
            return False
        
        # Check for job ID parameter
        query_params = parse_qs(parsed.query)
        if 'jk' not in query_params:
            return False
        
        # Ensure job ID is alphanumeric
        job_id = query_params['jk'][0]
        if not re.match(r'^[a-zA-Z0-9]+$', job_id):
            return False
        
        return True
        
    except Exception:
        return False