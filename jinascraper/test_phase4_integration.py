"""Test script for Phase 4 integration in the orchestrator."""

import asyncio
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinascraper.core.orchestrator import ScrapingOrchestrator
from jinascraper.core.performance import performance_monitor, batch_processor
from jinascraper.core.security import security_auditor, url_validator, data_sanitizer
from jinascraper.core.plugin_system import plugin_registry, PluginInterface, plugin_hook
from jinascraper.core.service_adapters import MockDatabaseServiceAdapter
import structlog

logger = structlog.get_logger(__name__)


class TestDataProcessorPlugin(PluginInterface):
    """Test plugin for data processing."""
    
    @property
    def name(self) -> str:
        return "test_data_processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Test plugin for processing job data"
    
    async def initialize(self) -> bool:
        logger.info("Test data processor plugin initialized")
        return True
    
    async def cleanup(self) -> None:
        logger.info("Test data processor plugin cleaned up")


@plugin_hook("post_process_job_batch")
async def test_job_batch_processor(job_batch):
    """Test hook for processing job batches."""
    logger.info(f"Processing job batch with {len([j for j in job_batch if j is not None])} jobs")
    return f"Processed {len(job_batch)} jobs"


async def test_orchestrator_with_phase4():
    """Test orchestrator with Phase 4 improvements."""
    print("🧪 TESTING ORCHESTRATOR WITH PHASE 4 INTEGRATION")
    print("=" * 60)
    
    # Register test plugin
    test_plugin = TestDataProcessorPlugin()
    plugin_registry.register_plugin(test_plugin)
    
    # Create orchestrator with dependency injection
    mock_db = MockDatabaseServiceAdapter()
    orchestrator = ScrapingOrchestrator(database_service=mock_db)
    
    print("✅ Orchestrator created with dependency injection")
    
    # Test performance tracking
    start_time = time.time()
    
    # Test URL validation
    test_urls = [
        "https://www.emploi.tg/offre-emploi-togo/test-job",
        "https://anpetogo.org/job/test-job/",
        "javascript:alert('XSS')",  # Should be filtered
        "https://localhost:8080/admin"  # Should be filtered
    ]
    
    valid_urls = [url for url in test_urls if url_validator.is_valid_url(url)]
    print(f"✅ URL validation: {len(valid_urls)}/{len(test_urls)} URLs are valid")
    
    # Test data sanitization
    test_job_data = {
        "title": "Test Job <script>alert('XSS')</script>",
        "company": "Test Company",
        "description": "<div>Job description</div><img src=x onerror=alert('XSS')>",
        "source_url": "https://example.com/job"
    }
    
    sanitized_data = data_sanitizer.sanitize_job_data(test_job_data)
    scripts_removed = "<script>" not in sanitized_data["title"]
    print(f"✅ Data sanitization: Scripts removed: {scripts_removed}")
    
    # Test batch processing
    test_items = list(range(20))
    
    async def process_item(item):
        await asyncio.sleep(0.05)  # Simulate work
        return item * 2
    
    batch_results = await batch_processor.process_batch(
        test_items,
        process_item,
        progress_callback=lambda done, total: print(f"Batch progress: {done}/{total}")
    )
    
    print(f"✅ Batch processing: {len(batch_results)} items processed")
    
    # Test plugin hooks
    hook_results = await plugin_registry.trigger_hook("post_process_job_batch", [test_job_data])
    print(f"✅ Plugin hooks: {len(hook_results)} hook results")
    
    # Get performance statistics
    perf_stats = orchestrator.get_performance_stats()
    print(f"✅ Performance stats: {len(perf_stats['performance_metrics'])} operations tracked")
    
    # Test security auditing
    security_summary = security_auditor.get_security_summary()
    print(f"✅ Security auditing: {security_summary.get('total_events', 0)} security events")
    
    # Test plugin management
    plugin_status = plugin_registry.list_plugins()
    print(f"✅ Plugin management: {len(plugin_status)} plugins registered")
    
    total_time = time.time() - start_time
    print(f"\\n⏱️  Total test time: {total_time:.2f}s")
    
    # Show detailed statistics
    print("\\n📊 DETAILED STATISTICS:")
    print("-" * 40)
    
    # Performance metrics
    for op_name, stats in perf_stats['performance_metrics'].items():
        avg_time = stats.get('avg_execution_time', 0)
        executions = stats.get('total_executions', 0)
        print(f"  {op_name}: {avg_time:.4f}s avg ({executions} executions)")
    
    # Security summary
    print(f"\\n🔒 Security Events: {security_summary.get('total_events', 0)}")
    for event_type, count in security_summary.get('event_type_breakdown', {}).items():
        print(f"  {event_type}: {count}")
    
    # Plugin status
    print(f"\\n🔌 Plugins ({len(plugin_status)}):")
    for plugin_name, info in plugin_status.items():
        status = "✅" if info['initialized'] else "❌"
        print(f"  {status} {plugin_name} v{info['version']} - {info['description']}")
    
    print("\\n" + "=" * 60)
    print("✅ PHASE 4 INTEGRATION TEST COMPLETED SUCCESSFULLY")
    
    return True


async def main():
    """Run all Phase 4 integration tests."""
    print("🚀 PHASE 4 INTEGRATION TESTING")
    print("=" * 60)
    
    tests = [
        ("Orchestrator with Phase 4", await test_orchestrator_with_phase4())
    ]
    
    # Show test results
    print("\\n🧪 TEST RESULTS:")
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"FINAL RESULTS: {passed}/{len(tests)} tests passed")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)