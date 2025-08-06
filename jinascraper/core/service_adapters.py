"""Service adapters that implement the abstract interfaces."""

from typing import Dict, List, Any, Optional
import structlog

from .interfaces import (
    ContentExtractorInterface,
    JobStructurerInterface,
    CacheManagerInterface,
    DatabaseServiceInterface
)
from ..services.jina_client import JinaClient
from ..services.listing_scraper import ListingScraper
from ..services.detail_scraper import DetailScraper
from ..services.gemini_service import GeminiService
from ..services.cache_manager import CacheManager
from ..services.database_service import DatabaseService

logger = structlog.get_logger(__name__)


class JinaContentExtractorAdapter(ContentExtractorInterface):
    """Adapter for Jina-based content extraction services."""
    
    def __init__(self, jina_client: JinaClient):
        self.jina_client = jina_client
        self.listing_scraper = ListingScraper(jina_client)
        self.detail_scraper = DetailScraper(jina_client)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.jina_client.__aenter__()
        await self.listing_scraper.__aenter__()
        await self.detail_scraper.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.jina_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.listing_scraper.__aexit__(exc_type, exc_val, exc_tb)
        await self.detail_scraper.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_content(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract content from a URL using Jina Reader.
        
        Args:
            url: URL to extract content from
            **kwargs: Additional parameters for extraction
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            source_site = kwargs.get('source_site', 'unknown')
            return await self.detail_scraper.extract_job_data(url, source_site)
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            return {"content": "", "error": str(e)}
    
    async def extract_job_urls(self, listing_url: str, source_name: str) -> List[str]:
        """
        Extract job URLs from a listing page using Jina Reader.
        
        Args:
            listing_url: URL of the job listing page
            source_name: Name of the job source
            
        Returns:
            List of job URLs found on the page
        """
        try:
            return await self.listing_scraper.extract_job_urls(listing_url, source_name)
        except Exception as e:
            logger.error(f"Job URL extraction failed for {listing_url}: {str(e)}")
            return []


class GeminiJobStructurerAdapter(JobStructurerInterface):
    """Adapter for Gemini-based job data structuring."""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
    
    async def structure_job_data(
        self, 
        raw_content: str, 
        source_url: str, 
        source_site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Structure raw job content using Gemini AI.
        
        Args:
            raw_content: Raw job content
            source_url: URL of the job posting
            source_site: Name of the source site
            
        Returns:
            Structured job data or None if structuring failed
        """
        try:
            return await self.gemini_service.structure_job_data(
                raw_content, source_url, source_site
            )
        except Exception as e:
            logger.error(f"Job structuring failed for {source_url}: {str(e)}")
            return None


class RedisCacheManagerAdapter(CacheManagerInterface):
    """Adapter for Redis-based cache management."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.cache_manager.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cache_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    async def is_url_scraped(self, url: str) -> bool:
        """
        Check if a URL has been scraped recently.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL has been scraped recently
        """
        try:
            return await self.cache_manager.is_url_scraped(url)
        except Exception as e:
            logger.error(f"Cache check failed for {url}: {str(e)}")
            return False
    
    async def mark_url_scraped(self, url: str, source_name: str) -> None:
        """
        Mark a URL as scraped.
        
        Args:
            url: URL to mark as scraped
            source_name: Name of the source
        """
        try:
            await self.cache_manager.mark_url_scraped(url, source_name)
        except Exception as e:
            logger.error(f"Cache marking failed for {url}: {str(e)}")
    
    async def filter_new_urls(self, urls: List[str], source_name: str) -> List[str]:
        """
        Filter out URLs that have been scraped recently.
        
        Args:
            urls: List of URLs to filter
            source_name: Name of the source
            
        Returns:
            List of URLs that haven't been scraped recently
        """
        try:
            return await self.cache_manager.filter_new_urls(urls, source_name)
        except Exception as e:
            logger.error(f"URL filtering failed for source {source_name}: {str(e)}")
            return urls  # Return all URLs if filtering fails


class DatabaseServiceAdapter(DatabaseServiceInterface):
    """Adapter for Supabase database service."""
    
    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
    
    async def upsert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Upsert a job offer to the database.
        
        Args:
            job_data: Job data to upsert
            
        Returns:
            Job record from database or None if failed
        """
        try:
            return await self.database_service.upsert_job(job_data)
        except Exception as e:
            logger.error(f"Database upsert failed: {str(e)}")
            return None
    
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]], source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Batch upsert jobs to the database.
        
        Args:
            jobs_data: List of job data to upsert
            source_name: Optional source identifier to pass to the database layer
            
        Returns:
            Batch operation results
        """
        try:
            return await self.database_service.upsert_jobs_batch(jobs_data, source_name)
        except Exception as e:
            logger.error(f"Database batch upsert failed: {str(e)}")
            return {"success": 0, "errors": len(jobs_data), "total": len(jobs_data)}
    
    async def update_scraping_stats(self, stats_data: Dict[str, Any]) -> bool:
        """
        Update scraping statistics in the database.
        
        Args:
            stats_data: Statistics data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.database_service.update_scraping_stats(stats_data)
        except Exception as e:
            logger.error(f"Database stats update failed: {str(e)}")
            return False


class MockDatabaseServiceAdapter(DatabaseServiceInterface):
    """Mock adapter for database services (for testing without database)."""
    
    def __init__(self):
        self.jobs_storage = []
        self.stats_storage = []
    
    async def upsert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mock upsert of a job offer.
        
        Args:
            job_data: Job data to upsert
            
        Returns:
            Mock job record
        """
        job_record = {**job_data, "id": f"mock_job_{len(self.jobs_storage)}"}
        self.jobs_storage.append(job_record)
        logger.info(f"Mock job upserted: {job_record.get('title', 'Unknown')}")
        return job_record
    
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mock batch upsert of jobs.
        
        Args:
            jobs_data: List of job data to upsert
            
        Returns:
            Mock batch operation results
        """
        for job_data in jobs_data:
            await self.upsert_job(job_data)
        
        result = {
            "success": len(jobs_data),
            "errors": 0,
            "total": len(jobs_data)
        }
        
        logger.info(f"Mock batch upsert completed: {result}")
        return result
    
    async def update_scraping_stats(self, stats_data: Dict[str, Any]) -> bool:
        """
        Mock update of scraping statistics.
        
        Args:
            stats_data: Statistics data to update
            
        Returns:
            Always True for mock
        """
        self.stats_storage.append(stats_data)
        logger.info(f"Mock stats updated: {stats_data.get('source_site', 'unknown')}")
        return True