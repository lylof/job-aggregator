"""Abstract interfaces for dependency injection and loose coupling."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
from ..models import JobOffer, ScrapingResult


class ContentExtractorInterface(ABC):
    """Abstract interface for content extraction services."""
    
    @abstractmethod
    async def extract_content(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            **kwargs: Additional parameters for extraction
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        pass
    
    @abstractmethod
    async def extract_job_urls(self, listing_url: str, source_name: str) -> List[str]:
        """
        Extract job URLs from a listing page.
        
        Args:
            listing_url: URL of the job listing page
            source_name: Name of the job source
            
        Returns:
            List of job URLs found on the page
        """
        pass


class JobStructurerInterface(ABC):
    """Abstract interface for job data structuring services."""
    
    @abstractmethod
    async def structure_job_data(
        self, 
        raw_content: str, 
        source_url: str, 
        source_site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Structure raw job content into standardized format.
        
        Args:
            raw_content: Raw job content
            source_url: URL of the job posting
            source_site: Name of the source site
            
        Returns:
            Structured job data or None if structuring failed
        """
        pass


class CacheManagerInterface(ABC):
    """Abstract interface for cache management services."""
    
    @abstractmethod
    async def is_url_scraped(self, url: str) -> bool:
        """
        Check if a URL has been scraped recently.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL has been scraped recently
        """
        pass
    
    @abstractmethod
    async def mark_url_scraped(self, url: str, source_name: str) -> None:
        """
        Mark a URL as scraped.
        
        Args:
            url: URL to mark as scraped
            source_name: Name of the source
        """
        pass
    
    @abstractmethod
    async def filter_new_urls(self, urls: List[str], source_name: str) -> List[str]:
        """
        Filter out URLs that have been scraped recently.
        
        Args:
            urls: List of URLs to filter
            source_name: Name of the source
            
        Returns:
            List of URLs that haven't been scraped recently
        """
        pass


class DatabaseServiceInterface(ABC):
    """Abstract interface for database services."""
    
    @abstractmethod
    async def upsert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert or update a job offer.
        
        Args:
            job_data: Job data to upsert
            
        Returns:
            Upserted job record or None if failed
        """
        pass
    
    @abstractmethod
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert or update multiple jobs in batch.
        
        Args:
            jobs_data: List of job data to upsert
            
        Returns:
            Dictionary with batch operation results
        """
        pass
    
    @abstractmethod
    async def update_scraping_stats(self, stats_data: Dict[str, Any]) -> bool:
        """
        Update scraping statistics.
        
        Args:
            stats_data: Statistics data to update
            
        Returns:
            True if update was successful
        """
        pass


class URLCleanerInterface(Protocol):
    """Protocol interface for URL cleaners."""
    
    def clean_urls(self, urls: List[str]) -> List[str]:
        """
        Clean and filter a list of URLs.
        
        Args:
            urls: List of URLs to clean
            
        Returns:
            List of cleaned and filtered URLs
        """
        ...


class ServiceContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, interface_name: str, implementation: Any, singleton: bool = True) -> None:
        """
        Register a service implementation.
        
        Args:
            interface_name: Name of the interface/service
            implementation: Implementation instance or factory
            singleton: Whether to use singleton pattern
        """
        self._services[interface_name] = {
            'implementation': implementation,
            'singleton': singleton
        }
    
    def get(self, interface_name: str) -> Any:
        """
        Get a service implementation.
        
        Args:
            interface_name: Name of the interface/service
            
        Returns:
            Service implementation instance
            
        Raises:
            KeyError: If service is not registered
        """
        if interface_name not in self._services:
            raise KeyError(f"Service '{interface_name}' not registered")
        
        service_config = self._services[interface_name]
        
        if service_config['singleton']:
            if interface_name not in self._singletons:
                implementation = service_config['implementation']
                if callable(implementation):
                    self._singletons[interface_name] = implementation()
                else:
                    self._singletons[interface_name] = implementation
            return self._singletons[interface_name]
        else:
            implementation = service_config['implementation']
            if callable(implementation):
                return implementation()
            else:
                return implementation
    
    def is_registered(self, interface_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            interface_name: Name of the interface/service
            
        Returns:
            True if service is registered
        """
        return interface_name in self._services


# Global service container instance
service_container = ServiceContainer()