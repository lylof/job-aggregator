"""URL cleaner for LinkedIn Togo job source."""

import re
from urllib.parse import urlparse, parse_qs
from typing import List


def clean_linkedin_togo_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to LinkedIn Togo.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    cleaned_urls = []
    
    for url in urls:
        # Basic cleaning
        url = clean_linkedin_togo_url(url)
        
        # Validate URL
        if is_valid_linkedin_togo_url(url) and url not in cleaned_urls:
            cleaned_urls.append(url)
    
    return cleaned_urls


def clean_linkedin_togo_url(url: str) -> str:
    """
    Clean a LinkedIn Togo URL specifically.
    
    Args:
        url: LinkedIn Togo URL to clean
        
    Returns:
        Cleaned LinkedIn Togo URL
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
        
        # Keep only job ID related parameters
        for param in ['currentJobId', 'refId', 'trackingId']:
            if param in query_params:
                essential_params[param] = query_params[param][0]
        
        # Reconstruct URL with only essential parameters
        if essential_params:
            query_string = '&'.join([f"{k}={v}" for k, v in essential_params.items()])
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query_string}"
        else:
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    return url


def is_valid_linkedin_togo_url(url: str) -> bool:
    """
    Validate that an URL is a valid LinkedIn Togo job offer URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is a valid LinkedIn Togo job offer URL
    """
    try:
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc not in ["tg.linkedin.com", "www.linkedin.com"]:
            return False
        
        # Check path pattern for job view
        if not re.match(r'^/jobs/view/[^/]+/?$', parsed.path):
            return False
        
        # Extract job ID from path
        job_id_match = re.search(r'/jobs/view/([^/]+)', parsed.path)
        if not job_id_match:
            return False
        
        # Ensure job ID is numeric or alphanumeric
        job_id = job_id_match.group(1)
        if not re.match(r'^[a-zA-Z0-9-]+$', job_id):
            return False
        
        return True
        
    except Exception:
        return False