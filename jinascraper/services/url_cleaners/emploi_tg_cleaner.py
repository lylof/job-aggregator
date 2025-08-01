"""URL cleaner for Emploi.tg job source."""

from typing import List
from .base_cleaner import PatternBasedURLCleaner


class EmploiTgCleaner(PatternBasedURLCleaner):
    """URL cleaner specifically for Emploi.tg job offers."""
    
    def __init__(self):
        valid_patterns = [
            r'^/offre-emploi-togo/[^/]+(-\d+)?/?$',
            r'^/offre-emploi/[^/]+(-\d+)?/?$',
            r'^/node/\d+/?$'
        ]
        super().__init__("emploi_tg", "www.emploi.tg", valid_patterns)
    
    def apply_source_specific_cleaning(self, url: str) -> str:
        """
        Apply Emploi.tg specific cleaning rules.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Apply base cleaning first
        url = super().apply_source_specific_cleaning(url)
        
        # Remove query parameters for Emploi.tg
        if '?' in url:
            url = url.split('?')[0]
        
        return url


# Create a singleton instance
_emploi_tg_cleaner = EmploiTgCleaner()


def clean_emploi_tg_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter job offer URLs specific to Emploi.tg.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    return _emploi_tg_cleaner.clean_urls(urls)