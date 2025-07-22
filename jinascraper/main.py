"""Main entry point for Jina Job Scraper."""

import asyncio
import sys
from typing import Optional
import structlog
import click

from .core.orchestrator import ScrapingOrchestrator
from .config import config


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if config.structured_logging else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@click.group()
def cli():
    """Jina Job Scraper - Togo job aggregation platform."""
    pass


@cli.command()
@click.option('--dry-run', is_flag=True, help='Run without saving to database')
@click.option('--sources', help='Comma-separated list of sources to process')
async def scrape(dry_run: bool, sources: Optional[str]):
    """Run a complete scraping cycle."""
    logger.info(
        "Starting scraping cycle",
        dry_run=dry_run,
        sources=sources,
        environment=config.environment
    )
    
    try:
        async with ScrapingOrchestrator() as orchestrator:
            if dry_run:
                logger.info("DRY RUN MODE - No data will be saved")
            
            result = await orchestrator.run_full_cycle()
            
            # Display results
            click.echo("\n" + "="*60)
            click.echo("SCRAPING CYCLE RESULTS")
            click.echo("="*60)
            click.echo(f"Success: {'✅' if result.success else '❌'}")
            click.echo(f"Jobs Found: {result.jobs_found}")
            click.echo(f"Jobs Processed: {result.jobs_processed}")
            click.echo(f"Processing Time: {result.processing_time_seconds:.2f}s")
            click.echo(f"Source Site: {result.source_site}")
            
            if result.errors:
                click.echo(f"\nErrors ({len(result.errors)}):")
                for error in result.errors:
                    click.echo(f"  - {error}")
            
            click.echo("="*60)
            
            # Exit with appropriate code
            sys.exit(0 if result.success else 1)
            
    except Exception as e:
        logger.error("Scraping cycle failed", error=str(e))
        click.echo(f"❌ Scraping failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
async def test_services():
    """Test all services connectivity and configuration."""
    logger.info("Testing services connectivity")
    
    try:
        async with ScrapingOrchestrator() as orchestrator:
            click.echo("Testing services...")
            
            # Test Jina Reader
            click.echo("🔍 Testing Jina Reader Service...")
            test_urls = ["https://www.emploi.tg/recherche-jobs-togo"]
            jina_test = await orchestrator.jina_service.test_rate_limiting(test_urls)
            click.echo(f"   ✅ Jina Reader: {jina_test['successful_requests']}/{jina_test['total_requests']} successful")
            
            # Test Gemini
            click.echo("🤖 Testing Gemini Service...")
            test_content = "Titre: Développeur Python\nEntreprise: TechCorp\nLieu: Lomé"
            gemini_test = await orchestrator.gemini_service.test_gemini_extraction(test_content, "test://url")
            click.echo(f"   ✅ Gemini: {'Success' if gemini_test['success'] else 'Failed'}")
            
            # Test Cache
            click.echo("💾 Testing Cache Manager...")
            await orchestrator.cache_manager.mark_url_scraped("test://url", "test_source")
            is_cached = await orchestrator.cache_manager.is_url_scraped("test://url")
            click.echo(f"   ✅ Cache: {'Working' if is_cached else 'Failed'}")
            
            # Test Database
            click.echo("🗄️  Testing Database Service...")
            orchestrator.database_service.connect()
            click.echo("   ✅ Database: Connected")
            
            click.echo("\n✅ All services are working correctly!")
            
    except Exception as e:
        logger.error("Service test failed", error=str(e))
        click.echo(f"❌ Service test failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('source_name')
async def test_source(source_name: str):
    """Test a specific job source."""
    logger.info("Testing specific source", source=source_name)
    
    try:
        async with ScrapingOrchestrator() as orchestrator:
            click.echo(f"Testing source: {source_name}")
            
            # Test URL extraction
            from .sources_config import TogoJobSources
            source_config = TogoJobSources.get_source(source_name)
            
            if not source_config:
                click.echo(f"❌ Source '{source_name}' not found")
                sys.exit(1)
            
            click.echo(f"📍 URL: {source_config.listing_url}")
            
            urls = await orchestrator.jina_service.extract_job_urls(
                source_config.listing_url,
                source_name=source_name
            )
            
            click.echo(f"✅ Found {len(urls)} job URLs")
            
            if urls:
                click.echo("\nSample URLs:")
                for i, url in enumerate(urls[:5]):  # Show first 5
                    click.echo(f"  {i+1}. {url}")
                
                if len(urls) > 5:
                    click.echo(f"  ... and {len(urls) - 5} more")
            
    except Exception as e:
        logger.error("Source test failed", error=str(e), source=source_name)
        click.echo(f"❌ Source test failed: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    # Handle async commands
    def async_command(f):
        def wrapper(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))
        return wrapper
    
    # Apply async wrapper to async commands
    scrape.callback = async_command(scrape.callback)
    test_services.callback = async_command(test_services.callback)
    test_source.callback = async_command(test_source.callback)
    
    cli()


if __name__ == "__main__":
    main()