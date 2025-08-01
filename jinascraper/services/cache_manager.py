"""Redis Cache Manager for delta scraping and URL deduplication."""

import asyncio
import hashlib
import json
import time
from typing import List, Optional, Dict, Any, Set
import structlog
from datetime import datetime, timedelta

from ..config import config
from .redis_factory import create_redis_client, test_redis_client, is_fake_redis, get_redis_info


logger = structlog.get_logger(__name__)


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheError):
    """Exception for Redis connection errors."""
    pass


class CacheManager:
    """Redis-based cache manager for delta scraping and deduplication."""
    
    def __init__(self):
        self.redis_url = config.redis_url
        self.redis_client = None
        
        # Cache TTL settings (7 days as per specs)
        self.url_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
        self.job_data_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
        
        # Key prefixes for organization
        self.scraped_prefix = "scraped"
        self.processed_prefix = "processed"
        self.source_prefix = "source"
        self.stats_prefix = "stats"
        
        logger.info("CacheManager initialized", redis_url=self.redis_url)
    
    async def connect(self):
        """Establish connection to Redis (real or fake)."""
        try:
            # Create Redis client using factory
            self.redis_client = create_redis_client(self.redis_url)
            
            # Test connection
            connection_test = await test_redis_client(self.redis_client)
            if not connection_test:
                raise CacheConnectionError("Redis client test failed")
            
            # Log connection info
            redis_info = get_redis_info(self.redis_client)
            logger.info("Redis connection established successfully", 
                       redis_type=redis_info["type"],
                       is_fake=redis_info["is_fake"])
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise CacheConnectionError(f"Redis connection failed: {str(e)}")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def _hash_url(self, url: str) -> str:
        """Create a hash for URL to use as cache key."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _get_scraped_key(self, url: str) -> str:
        """Get Redis key for scraped URL tracking."""
        url_hash = self._hash_url(url)
        return f"{self.scraped_prefix}:{url_hash}"
    
    def _get_processed_key(self, job_id: str) -> str:
        """Get Redis key for processed job data."""
        return f"{self.processed_prefix}:{job_id}"
    
    def _get_source_key(self, source_name: str) -> str:
        """Get Redis key for source-specific data."""
        return f"{self.source_prefix}:{source_name}"
    
    def _get_stats_key(self, date_str: str) -> str:
        """Get Redis key for daily statistics."""
        return f"{self.stats_prefix}:{date_str}"
    
    async def is_url_scraped(self, url: str) -> bool:
        """
        Check if a URL has already been scraped recently.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL was scraped within TTL period
        """
        try:
            key = self._get_scraped_key(url)
            exists = await self.redis_client.exists(key)
            
            logger.debug("URL scrape status checked", url=url, already_scraped=bool(exists))
            return bool(exists)
            
        except Exception as e:
            logger.error("Failed to check URL scrape status", url=url, error=str(e))
            # On error, assume not scraped to avoid missing URLs
            return False
    
    async def mark_url_scraped(self, url: str, source_name: str = None) -> bool:
        """
        Mark a URL as scraped with TTL.
        
        Args:
            url: URL to mark as scraped
            source_name: Optional source name for tracking
            
        Returns:
            True if successfully marked
        """
        try:
            key = self._get_scraped_key(url)
            
            # Store with metadata
            data = {
                "url": url,
                "scraped_at": datetime.utcnow().isoformat(),
                "source": source_name or "unknown"
            }
            
            await self.redis_client.setex(
                key, 
                self.url_ttl, 
                json.dumps(data)
            )
            
            logger.debug("URL marked as scraped", url=url, source=source_name)
            return True
            
        except Exception as e:
            logger.error("Failed to mark URL as scraped", url=url, error=str(e))
            return False
    
    async def filter_new_urls(self, urls: List[str], source_name: str = None) -> List[str]:
        """
        Filter out URLs that have already been scraped.
        
        Args:
            urls: List of URLs to filter
            source_name: Source name for logging
            
        Returns:
            List of URLs that haven't been scraped recently
        """
        if not urls:
            return []
        
        try:
            # Check all URLs in batch for efficiency
            keys = [self._get_scraped_key(url) for url in urls]
            exists_results = await self.redis_client.mget(keys)
            
            # Filter out URLs that exist in cache
            new_urls = []
            for i, (url, exists) in enumerate(zip(urls, exists_results)):
                if not exists:
                    new_urls.append(url)
            
            logger.info(
                "URLs filtered for delta scraping",
                source=source_name,
                total_urls=len(urls),
                new_urls=len(new_urls),
                already_scraped=len(urls) - len(new_urls)
            )
            
            return new_urls
            
        except Exception as e:
            logger.error("Failed to filter URLs", source=source_name, error=str(e))
            # On error, return all URLs to avoid missing data
            return urls
    
    async def store_job_data(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Store processed job data in cache.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary
            
        Returns:
            True if successfully stored
        """
        try:
            key = self._get_processed_key(job_id)
            
            # Add cache metadata
            cached_data = {
                **job_data,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.job_data_ttl
            }
            
            await self.redis_client.setex(
                key,
                self.job_data_ttl,
                json.dumps(cached_data, default=str)
            )
            
            logger.debug("Job data cached", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("Failed to cache job data", job_id=job_id, error=str(e))
            return False
    
    async def get_job_data(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached job data.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data dictionary or None if not found
        """
        try:
            key = self._get_processed_key(job_id)
            data = await self.redis_client.get(key)
            
            if data:
                job_data = json.loads(data)
                logger.debug("Job data retrieved from cache", job_id=job_id)
                return job_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to retrieve job data", job_id=job_id, error=str(e))
            return None
    
    async def update_source_stats(self, source_name: str, stats: Dict[str, Any]) -> bool:
        """
        Update statistics for a source.
        
        Args:
            source_name: Name of the source
            stats: Statistics dictionary
            
        Returns:
            True if successfully updated
        """
        try:
            key = self._get_source_key(source_name)
            
            # Get existing stats
            existing_data = await self.redis_client.get(key)
            if existing_data:
                existing_stats = json.loads(existing_data)
            else:
                existing_stats = {}
            
            # Merge with new stats
            updated_stats = {
                **existing_stats,
                **stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.setex(
                key,
                self.url_ttl,
                json.dumps(updated_stats, default=str)
            )
            
            logger.debug("Source stats updated", source=source_name, stats=stats)
            return True
            
        except Exception as e:
            logger.error("Failed to update source stats", source=source_name, error=str(e))
            return False
    
    async def get_source_stats(self, source_name: str) -> Dict[str, Any]:
        """
        Get statistics for a source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Statistics dictionary
        """
        try:
            key = self._get_source_key(source_name)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return {}
            
        except Exception as e:
            logger.error("Failed to get source stats", source=source_name, error=str(e))
            return {}
    
    async def cleanup_expired_keys(self) -> Dict[str, int]:
        """
        Clean up expired keys and return cleanup statistics.
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cleanup_stats = {
                "scraped_keys_cleaned": 0,
                "processed_keys_cleaned": 0,
                "total_keys_before": 0,
                "total_keys_after": 0
            }
            
            # Get total keys before cleanup
            cleanup_stats["total_keys_before"] = await self.redis_client.dbsize()
            
            # Redis automatically handles TTL expiration, but we can force cleanup
            # by scanning for expired keys (this is optional as Redis handles it)
            
            # Scan for potentially expired scraped keys
            async for key in self.redis_client.scan_iter(match=f"{self.scraped_prefix}:*"):
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    cleanup_stats["scraped_keys_cleaned"] += 1
            
            # Scan for potentially expired processed keys
            async for key in self.redis_client.scan_iter(match=f"{self.processed_prefix}:*"):
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    cleanup_stats["processed_keys_cleaned"] += 1
            
            cleanup_stats["total_keys_after"] = await self.redis_client.dbsize()
            
            logger.info("Cache cleanup completed", stats=cleanup_stats)
            return cleanup_stats
            
        except Exception as e:
            logger.error("Failed to cleanup cache", error=str(e))
            return {"error": str(e)}
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get comprehensive cache information and statistics.
        
        Returns:
            Dictionary with cache information
        """
        try:
            info = await self.redis_client.info()
            
            # Count keys by prefix
            scraped_count = 0
            processed_count = 0
            source_count = 0
            
            async for key in self.redis_client.scan_iter(match=f"{self.scraped_prefix}:*"):
                scraped_count += 1
            
            async for key in self.redis_client.scan_iter(match=f"{self.processed_prefix}:*"):
                processed_count += 1
            
            async for key in self.redis_client.scan_iter(match=f"{self.source_prefix}:*"):
                source_count += 1
            
            cache_info = {
                "redis_info": {
                    "version": info.get("redis_version"),
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed")
                },
                "key_counts": {
                    "scraped_urls": scraped_count,
                    "processed_jobs": processed_count,
                    "source_stats": source_count,
                    "total_keys": await self.redis_client.dbsize()
                },
                "ttl_settings": {
                    "url_ttl_days": self.url_ttl / (24 * 60 * 60),
                    "job_data_ttl_days": self.job_data_ttl / (24 * 60 * 60)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return cache_info
            
        except Exception as e:
            logger.error("Failed to get cache info", error=str(e))
            return {"error": str(e)}
    
    async def test_cache_operations(self) -> Dict[str, Any]:
        """
        Test basic cache operations for validation.
        
        Returns:
            Test results dictionary
        """
        test_results = {
            "connection": False,
            "write_operation": False,
            "read_operation": False,
            "delete_operation": False,
            "url_filtering": False,
            "error": None
        }
        
        try:
            # Test connection
            await self.redis_client.ping()
            test_results["connection"] = True
            
            # Test write operation
            test_key = "test:cache_manager"
            test_data = {"test": "data", "timestamp": time.time()}
            await self.redis_client.setex(test_key, 60, json.dumps(test_data))
            test_results["write_operation"] = True
            
            # Test read operation
            retrieved_data = await self.redis_client.get(test_key)
            if retrieved_data:
                parsed_data = json.loads(retrieved_data)
                if parsed_data.get("test") == "data":
                    test_results["read_operation"] = True
            
            # Test delete operation
            deleted = await self.redis_client.delete(test_key)
            if deleted:
                test_results["delete_operation"] = True
            
            # Test URL filtering
            test_urls = ["http://test1.com", "http://test2.com", "http://test3.com"]
            await self.mark_url_scraped(test_urls[0], "test_source")
            
            filtered_urls = await self.filter_new_urls(test_urls, "test_source")
            if len(filtered_urls) == 2:  # Should filter out the first URL
                test_results["url_filtering"] = True
            
            # Cleanup test data
            await self.redis_client.delete(self._get_scraped_key(test_urls[0]))
            
            logger.info("Cache operations test completed", results=test_results)
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error("Cache operations test failed", error=str(e))
        
        return test_results