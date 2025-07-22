"""Test script for Phase 3 improvements."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinascraper.core.external_services import ResilientCacheService
from jinascraper.core.interfaces import service_container
from jinascraper.core.service_adapters import MockDatabaseServiceAdapter


async def test_resilient_cache():
    """Test resilient cache service with fallback."""
    print("🧪 Testing resilient cache service...")
    
    # Test with invalid Redis URL to trigger fallback
    cache = ResilientCacheService('redis://invalid:6379')
    
    # Test set/get operations
    await cache.set('test_key', 'test_value', ttl=60)
    result = await cache.get('test_key')
    
    print(f"✅ Cache fallback test: {result}")
    return result == 'test_value'


def test_dependency_injection():
    """Test dependency injection container."""
    print("🧪 Testing dependency injection...")
    
    # Register a service
    service_container.register('test_db', MockDatabaseServiceAdapter())
    
    # Retrieve the service
    db_service = service_container.get('test_db')
    
    print(f"✅ DI test: {type(db_service).__name__}")
    return isinstance(db_service, MockDatabaseServiceAdapter)


async def test_orchestrator_with_di():
    """Test orchestrator with dependency injection."""
    print("🧪 Testing orchestrator with DI...")
    
    from jinascraper.core.orchestrator import ScrapingOrchestrator
    
    # Create orchestrator with default services
    orchestrator = ScrapingOrchestrator()
    
    print(f"✅ Orchestrator DI test: {type(orchestrator.content_extractor).__name__}")
    return True


async def main():
    """Run all Phase 3 tests."""
    print("🚀 PHASE 3 ARCHITECTURE TESTS")
    print("=" * 50)
    
    tests = [
        ("Dependency Injection", test_dependency_injection()),
        ("Resilient Cache", await test_resilient_cache()),
        ("Orchestrator with DI", await test_orchestrator_with_di())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)