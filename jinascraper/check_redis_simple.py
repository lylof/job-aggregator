#!/usr/bin/env python3
"""Simple Redis check without complex imports."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

async def test_redis_simple():
    """Simple Redis connection test."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"🔍 Testing Redis connection to: {redis_url}")
    
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # Test ping
        result = await client.ping()
        print(f"✅ Redis PING successful: {result}")
        
        # Test basic operations
        await client.set("test_key", "test_value", ex=10)
        value = await client.get("test_key")
        print(f"✅ Redis SET/GET successful: {value}")
        
        # Clean up
        await client.delete("test_key")
        await client.close()
        
        print("✅ Redis is fully functional!")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def suggest_fakeredis():
    """Suggest FakeRedis setup."""
    print("\n💡 FakeRedis Setup Recommendation:")
    print("=" * 40)
    
    print("1. Install FakeRedis:")
    print("   pip install fakeredis[json]")
    
    print("\n2. Add to requirements.txt:")
    print("   fakeredis[json]>=2.20.0  # For development")
    
    print("\n3. Test FakeRedis:")
    
    test_code = '''
import asyncio
import fakeredis.aioredis

async def test_fakeredis():
    fake_redis = fakeredis.aioredis.FakeRedis(
        encoding="utf-8",
        decode_responses=True
    )
    
    await fake_redis.set("test", "value")
    result = await fake_redis.get("test")
    print(f"FakeRedis test: {result}")

asyncio.run(test_fakeredis())
'''
    
    print(test_code)

async def main():
    print("🚀 Redis Status Check for JinaScraper")
    print("=" * 40)
    
    redis_working = await test_redis_simple()
    
    if not redis_working:
        suggest_fakeredis()
        
        print("\n🔧 Next Steps:")
        print("1. Install Redis server locally, OR")
        print("2. Use FakeRedis for development, OR") 
        print("3. Use Docker: docker run -d -p 6379:6379 redis:alpine")
    
    return redis_working

if __name__ == "__main__":
    asyncio.run(main())