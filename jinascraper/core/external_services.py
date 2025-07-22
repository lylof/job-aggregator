"""Abstractions for external services with fallback mechanisms."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import structlog
import asyncio
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class ExternalServiceError(Exception):
    """Base exception for external service errors."""
    pass


class CacheServiceInterface(ABC):
    """Abstract interface for cache services."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        pass


class DatabaseServiceInterface(ABC):
    """Abstract interface for database services."""
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a database query."""
        pass
    
    @abstractmethod
    async def insert_record(self, table: str, data: Dict[str, Any]) -> Optional[str]:
        """Insert a record and return its ID."""
        pass
    
    @abstractmethod
    async def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record by ID."""
        pass
    
    @abstractmethod
    async def upsert_record(self, table: str, data: Dict[str, Any], conflict_keys: List[str]) -> Optional[str]:
        """Insert or update a record based on conflict keys."""
        pass


class ResilientCacheService(CacheServiceInterface):
    """Cache service with fallback to in-memory cache when Redis is unavailable."""
    
    def __init__(self, redis_url: str, fallback_ttl: int = 3600):
        self.redis_url = redis_url
        self.fallback_ttl = fallback_ttl
        self.redis_client = None
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_available = True
        self.last_redis_check = datetime.now()
        self.redis_check_interval = timedelta(minutes=5)
    
    async def _get_redis_client(self):
        """Get Redis client with connection retry."""
        if self.redis_client is None:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.redis_available = True
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}")
                self.redis_available = False
                self.redis_client = None
        return self.redis_client
    
    async def _check_redis_availability(self) -> bool:
        """Check if Redis is available with periodic retry."""
        now = datetime.now()
        if not self.redis_available and (now - self.last_redis_check) > self.redis_check_interval:
            self.last_redis_check = now
            try:
                client = await self._get_redis_client()
                if client:
                    await client.ping()
                    self.redis_available = True
                    logger.info("Redis connection restored")
            except Exception:
                self.redis_available = False
        
        return self.redis_available
    
    def _clean_fallback_cache(self):
        """Clean expired entries from fallback cache."""
        now = datetime.now()
        expired_keys = [
            key for key, data in self.fallback_cache.items()
            if data.get('expires_at') and now > data['expires_at']
        ]
        for key in expired_keys:
            del self.fallback_cache[key]
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache with Redis fallback."""
        try:
            if await self._check_redis_availability():
                client = await self._get_redis_client()
                if client:
                    value = await client.get(key)
                    return value.decode('utf-8') if value else None
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {str(e)}")
            self.redis_available = False
        
        # Fallback to in-memory cache
        self._clean_fallback_cache()
        cache_entry = self.fallback_cache.get(key)
        if cache_entry:
            if not cache_entry.get('expires_at') or datetime.now() < cache_entry['expires_at']:
                return cache_entry['value']
            else:
                del self.fallback_cache[key]
        
        return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with Redis fallback."""
        try:
            if await self._check_redis_availability():
                client = await self._get_redis_client()
                if client:
                    if ttl:
                        await client.setex(key, ttl, value)
                    else:
                        await client.set(key, value)
                    return True
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {str(e)}")
            self.redis_available = False
        
        # Fallback to in-memory cache
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.fallback_cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            if await self._check_redis_availability():
                client = await self._get_redis_client()
                if client:
                    return bool(await client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists check failed for key {key}: {str(e)}")
            self.redis_available = False
        
        # Fallback to in-memory cache
        self._clean_fallback_cache()
        return key in self.fallback_cache
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        success = False
        
        try:
            if await self._check_redis_availability():
                client = await self._get_redis_client()
                if client:
                    success = bool(await client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete failed for key {key}: {str(e)}")
            self.redis_available = False
        
        # Also delete from fallback cache
        if key in self.fallback_cache:
            del self.fallback_cache[key]
            success = True
        
        return success


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        elif self.state == 'HALF_OPEN':
            return True
        return False
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class ResilientExternalService:
    """Base class for resilient external services with circuit breaker."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker()
    
    async def execute_with_circuit_breaker(self, operation, *args, **kwargs):
        """Execute an operation with circuit breaker protection."""
        if not self.circuit_breaker.can_execute():
            raise ExternalServiceError(f"{self.service_name} circuit breaker is OPEN")
        
        try:
            result = await operation(*args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"{self.service_name} operation failed: {str(e)}")
            raise ExternalServiceError(f"{self.service_name} operation failed: {str(e)}")


# Factory functions for creating resilient services
def create_resilient_cache_service(redis_url: str) -> ResilientCacheService:
    """Create a resilient cache service with Redis fallback."""
    return ResilientCacheService(redis_url)


def create_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Create a circuit breaker for a service."""
    return CircuitBreaker()