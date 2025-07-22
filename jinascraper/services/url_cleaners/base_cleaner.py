"""Base class for URL cleaners to eliminate code duplication."""

import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from typing import List, Pattern
import structlog

logger = structlog.get_logger(__name__)


class BaseURLCleaner(ABC):
    """
    Abstract base class for URL cleaners.
    
    This class provides common functionality for cleaning and validating URLs,
    while allowing specific implementations for different job sources.
    """
    
    def __init__(self, source_name: str, domain: str):
        """
        Initialize the URL cleaner.
        
        Args:
            source_name: Name of the job source
            domain: Expected domain for URLs
        """
        self.source_name = source_name
        self.domain = domain
    
    def clean_urls(self, urls: List[str]) -> List[str]:
        """
        Clean and filter a list of URLs.
        
        Args:
            urls: List of URLs to clean
            
        Returns:
            List of cleaned and filtered URLs
        """
        cleaned_urls = []
        
        for url in urls:
            try:
                # Basic cleaning
                cleaned_url = self.clean_single_url(url)
                
                # Validate URL
                if self.is_valid_url(cleaned_url) and cleaned_url not in cleaned_urls:
                    cleaned_urls.append(cleaned_url)
                    
            except Exception as e:
                logger.warning(
                    f"Error cleaning URL for {self.source_name}",
                    url=url,
                    error=str(e)
                )
                continue
        
        logger.info(
            f"URL cleaning completed for {self.source_name}",
            original_count=len(urls),
            cleaned_count=len(cleaned_urls)
        )
        
        return cleaned_urls
    
    def clean_single_url(self, url: str) -> str:
        """
        Clean a single URL using common cleaning rules.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Remove problematic characters at the end
        url = re.sub(r'[.,;:!?)\\]$', '', url)
        
        # Remove trailing parenthesis
        url = url.rstrip(')')
        
        # Apply source-specific cleaning
        url = self.apply_source_specific_cleaning(url)
        
        return url.strip()
    
    def is_valid_url(self, url: str) -> bool:
        """
        Validate that a URL is valid for this source.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid for this source
        """
        try:
            parsed = urlparse(url)
            
            # Basic URL structure validation
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check if scheme is HTTP/HTTPS
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Check domain
            if not self.is_valid_domain(parsed.netloc):
                return False
            
            # Apply source-specific validation
            return self.apply_source_specific_validation(parsed)
            
        except Exception as e:
            logger.debug(f"URL validation failed for {url}: {str(e)}")
            return False
    
    def is_valid_domain(self, netloc: str) -> bool:
        """
        Check if the domain is valid for this source.
        
        Args:
            netloc: Network location from parsed URL
            
        Returns:
            True if domain is valid
        """
        netloc_lower = netloc.lower()
        domain_lower = self.domain.lower()
        
        # Direct match
        if netloc_lower == domain_lower:
            return True
        
        # Subdomain match (e.g., www.example.com matches example.com)
        if netloc_lower.endswith(f".{domain_lower}"):
            return True
        
        # Reverse subdomain match (e.g., example.com matches www.example.com)
        if domain_lower.endswith(f".{netloc_lower}"):
            return True
        
        return False
    
    @abstractmethod
    def apply_source_specific_cleaning(self, url: str) -> str:
        """
        Apply source-specific URL cleaning rules.
        
        Args:
            url: URL to clean
            
        Returns:
            URL after applying source-specific cleaning
        """
        pass
    
    @abstractmethod
    def apply_source_specific_validation(self, parsed_url) -> bool:
        """
        Apply source-specific URL validation rules.
        
        Args:
            parsed_url: Parsed URL object from urlparse
            
        Returns:
            True if URL passes source-specific validation
        """
        pass


class PatternBasedURLCleaner(BaseURLCleaner):
    """
    URL cleaner that uses regex patterns for validation.
    
    This is a concrete implementation that can be used for sources
    that follow predictable URL patterns.
    """
    
    def __init__(self, source_name: str, domain: str, valid_patterns: List[str]):
        """
        Initialize the pattern-based URL cleaner.
        
        Args:
            source_name: Name of the job source
            domain: Expected domain for URLs
            valid_patterns: List of regex patterns for valid URLs
        """
        super().__init__(source_name, domain)
        self.valid_patterns = [re.compile(pattern) for pattern in valid_patterns]
    
    def apply_source_specific_cleaning(self, url: str) -> str:
        """
        Apply basic cleaning (can be overridden by subclasses).
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Remove URL fragments
        if '#' in url:
            url = url.split('#')[0]
        
        return url
    
    def apply_source_specific_validation(self, parsed_url) -> bool:
        """
        Validate URL against the configured patterns.
        
        Args:
            parsed_url: Parsed URL object from urlparse
            
        Returns:
            True if URL matches any of the valid patterns
        """
        path = parsed_url.path
        
        for pattern in self.valid_patterns:
            if pattern.match(path):
                return True
        
        return False