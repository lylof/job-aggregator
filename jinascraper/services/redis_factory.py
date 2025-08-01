"""Redis factory with FakeRedis fallback for development."""

import os
from typing import Union, Optional
import structlog

logger = structlog.get_logger(__name__)


def create_redis_client(redis_url: Optional[str] = None, force_fake: bool = None) -> Union['redis.asyncio.Redis', 'fakeredis.aioredis.FakeRedis']:
    """
    Create Redis client with FakeRedis fallback for development.
    
    Args:
        redis_url: Redis connection URL
        force_fake: Force FakeRedis usage (overrides environment)
        
    Returns:
        Redis client (real or fake)
    """
    redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Check if FakeRedis is forced via parameter or environment
    use_fake = force_fake or os.getenv("USE_FAKE_REDIS", "false").lower() == "true"
    
    if use_fake:
        logger.info("FakeRedis forced via configuration")
        return _create_fake_redis()
    
    # Try real Redis first
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection with a quick ping (non-blocking)
        # Note: We can't test async connection here, so we'll let the CacheManager handle it
        logger.info("Real Redis client created", url=redis_url)
        return client
        
    except ImportError as e:
        logger.error("Redis library not available", error=str(e))
        return _create_fake_redis()
    except Exception as e:
        logger.warning("Redis client creation failed, falling back to FakeRedis", error=str(e))
        return _create_fake_redis()


def _create_fake_redis() -> 'fakeredis.aioredis.FakeRedis':
    """Create FakeRedis client."""
    try:
        import fakeredis.aioredis
        
        fake_client = fakeredis.aioredis.FakeRedis(
            encoding="utf-8",
            decode_responses=True,
            # Enable JSON support if available
            version=(7, 0, 0)  # Simulate Redis 7.0
        )
        
        logger.info("FakeRedis client created for development")
        return fake_client
        
    except ImportError:
        logger.error("FakeRedis not installed. Install with: pip install fakeredis[json]")
        raise ImportError("Neither Redis nor FakeRedis is available")


async def test_redis_client(client) -> bool:
    """
    Test Redis client functionality.
    
    Args:
        client: Redis client to test
        
    Returns:
        True if client is working
    """
    try:
        # Test ping
        await client.ping()
        
        # Test basic operations
        test_key = "test:redis_factory"
        await client.set(test_key, "test_value", ex=10)
        value = await client.get(test_key)
        await client.delete(test_key)
        
        if value == "test_value":
            logger.info("Redis client test successful")
            return True
        else:
            logger.error("Redis client test failed: unexpected value", expected="test_value", got=value)
            return False
            
    except Exception as e:
        logger.error("Redis client test failed", error=str(e))
        return False


def is_fake_redis(client) -> bool:
    """
    Check if the client is FakeRedis.
    
    Args:
        client: Redis client to check
        
    Returns:
        True if client is FakeRedis
    """
    return "fakeredis" in str(type(client))


def get_redis_info(client) -> dict:
    """
    Get Redis client information.
    
    Args:
        client: Redis client
        
    Returns:
        Dictionary with client information
    """
    return {
        "type": "FakeRedis" if is_fake_redis(client) else "Real Redis",
        "class": str(type(client)),
        "is_fake": is_fake_redis(client)
    }