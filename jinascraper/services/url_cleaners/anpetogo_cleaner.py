"""URL cleaner for ANPE Togo job source."""

from ...utils.type_helpers import List
from .base_cleaner import PatternBasedURLCleaner


class AnpeTogoCleaner(PatternBasedURLCleaner):
    """URL cleaner specifically for ANPE Togo job offers."""
    
    def __init__(self):
        valid_patterns = [
            r'^/job/[^/]+/?$'  # Pattern for /job/job-title/
        ]
        super().__init__("anpetogo", "anpetogo.org", valid_patterns)
    
    def apply_source_specific_cleaning(self, url: str) -> str:
        """
        Apply ANPE Togo specific cleaning rules.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Apply base cleaning first
        url = super().apply_source_specific_cleaning(url)
        
        # Ensure URL ends with / for ANPE Togo
        if not url.endswith('/'):
            url += '/'
        
        return url
    
    def apply_source_specific_validation(self, parsed_url) -> bool:
        """
        Apply ANPE Togo specific validation rules.
        
        Args:
            parsed_url: Parsed URL object from urlparse
            
        Returns:
            True if URL passes ANPE Togo specific validation
        """
        # Check if it's a job URL with non-empty slug
        if "/job/" in parsed_url.path:
            job_slug = parsed_url.path.split("/job/")[-1].rstrip('/')
            return len(job_slug) > 0
        
        return super().apply_source_specific_validation(parsed_url)


# Create a singleton instance
_anpe_togo_cleaner = AnpeTogoCleaner()


def clean_anpe_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to ANPE Togo.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    return _anpe_togo_cleaner.clean_urls(urls)