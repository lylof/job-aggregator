"""Main scraping orchestrator that coordinates all services."""

import asyncio
import time
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import structlog

from ..services.jina_client import JinaClient
from ..services.listing_scraper import ListingScraper
from ..services.detail_scraper import DetailScraper
from ..services.gemini_service import GeminiService
from ..services.cache_manager import CacheManager
# from ..services.database_service import DatabaseService  # Temporairement désactivé
from ..config import SourceRegistry
from ..models import ScrapingResult, ExtractionMethod
from .performance import performance_tracked, batch_processor, performance_monitor
from .security import security_auditor, url_validator, data_sanitizer, validate_url_input, SecurityEvent
from .plugin_system import plugin_registry


logger = structlog.get_logger(__name__)


class ScrapingOrchestrator:
    """
    Main orchestrator that coordinates the two-stage scraping workflow:
    Stage 1: Exploration (URL discovery) 
    Stage 2: Analysis (Content extraction and structuring)
    """
    
    def __init__(
        self,
        content_extractor=None,
        job_structurer=None,
        cache_manager=None,
        database_service=None
    ):
        """
        Initialize the orchestrator with dependency injection.
        
        Args:
            content_extractor: Service for content extraction
            job_structurer: Service for job data structuring
            cache_manager: Service for cache management
            database_service: Service for database operations
        """
        # Use dependency injection or create default services
        from .interfaces import service_container
        from .service_adapters import (
            JinaContentExtractorAdapter,
            GeminiJobStructurerAdapter,
            RedisCacheManagerAdapter,
            MockDatabaseServiceAdapter
        )
        from ..services.jina_client import JinaClient
        from ..services.gemini_service import GeminiService
        from ..services.cache_manager import CacheManager
        
        # Initialize services with dependency injection
        self.content_extractor = content_extractor or JinaContentExtractorAdapter(JinaClient())
        self.job_structurer = job_structurer or GeminiJobStructurerAdapter(GeminiService())
        self.cache_manager = cache_manager or RedisCacheManagerAdapter(CacheManager())
        self.database_service = database_service or MockDatabaseServiceAdapter()
        
        # Orchestrator state
        self.current_cycle_id = None
        self.cycle_start_time = None
        self.cycle_metrics = {}
        
        logger.info("ScrapingOrchestrator initialized")
        
        # Initialize plugins
        asyncio.create_task(self._initialize_plugins())
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize services that support async context management
        if hasattr(self.content_extractor, '__aenter__'):
            await self.content_extractor.__aenter__()
        if hasattr(self.cache_manager, '__aenter__'):
            await self.cache_manager.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Clean up services that support async context management
        if hasattr(self.content_extractor, '__aexit__'):
            await self.content_extractor.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self.cache_manager, '__aexit__'):
            await self.cache_manager.__aexit__(exc_type, exc_val, exc_tb)
        
        # Cleanup plugins
        await plugin_registry.cleanup_all_plugins()
    
    async def _initialize_plugins(self):
        """Initialize available plugins."""
        try:
            # Initialize all registered plugins
            results = await plugin_registry.initialize_all_plugins()
            
            initialized_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            logger.info(f"Plugin initialization completed: {initialized_count}/{total_count} plugins initialized")
            
            # Log plugin status
            for plugin_name, success in results.items():
                if success:
                    logger.info(f"Plugin {plugin_name} initialized successfully")
                else:
                    logger.error(f"Plugin {plugin_name} failed to initialize")
                    
        except Exception as e:
            logger.error(f"Plugin initialization failed: {str(e)}")
    
    @performance_tracked("orchestrator.full_cycle")
    async def run_full_cycle(self) -> ScrapingResult:
        """
        Execute a complete scraping cycle: Stage 1 → Stage 2 → Storage.
        
        Returns:
            ScrapingResult with metrics and status
        """
        self.cycle_start_time = time.time()
        self.current_cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("Starting full scraping cycle", cycle_id=self.current_cycle_id)
        
        try:
            # Stage 1: Exploration - Discover job URLs
            stage1_result = await self.run_stage1_exploration()
            
            # Stage 2: Analysis - Extract and structure job data
            stage2_result = await self.run_stage2_analysis(stage1_result["new_urls"])
            
            # Generate final metrics
            cycle_result = self._generate_cycle_result(stage1_result, stage2_result)
            
            # Update scraping statistics
            await self._update_scraping_stats(cycle_result)
            
            logger.info(
                "Full scraping cycle completed",
                cycle_id=self.current_cycle_id,
                total_time_seconds=cycle_result.processing_time_seconds,
                jobs_processed=cycle_result.jobs_processed,
                success=cycle_result.success
            )
            
            return cycle_result
            
        except Exception as e:
            logger.error(
                "Full scraping cycle failed",
                cycle_id=self.current_cycle_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return error result
            return ScrapingResult(
                success=False,
                jobs_found=0,
                jobs_processed=0,
                errors=[f"Cycle failed: {str(e)}"],
                processing_time_seconds=time.time() - self.cycle_start_time,
                source_site="all_sources"
            )
    
    @performance_tracked("orchestrator.stage1_exploration")
    async def run_stage1_exploration(self) -> Dict[str, Any]:
        """
        Stage 1: Exploration - Extract job URLs from all configured sources.
        
        Returns:
            Dictionary with discovered URLs and metrics
        """
        logger.info("Starting Stage 1: Exploration", cycle_id=self.current_cycle_id)
        stage1_start = time.time()
        
        # Get all active sources
        sources = SourceRegistry.get_active_sources()
        
        # Extract URLs from all sources using content extractor
        source_urls = await self._extract_urls_from_all_sources(sources)
        
        # Apply delta filtering using cache
        all_discovered_urls = []
        new_urls_by_source = {}
        
        for source_name, urls in source_urls.items():
            if urls:
                # Filter out already processed URLs
                new_urls = await self.cache_manager.filter_new_urls(urls, source_name)
                new_urls_by_source[source_name] = new_urls
                all_discovered_urls.extend(new_urls)
                
                # Mark URLs as discovered in cache
                for url in new_urls:
                    await self.cache_manager.mark_url_scraped(url, source_name)
        
        stage1_time = time.time() - stage1_start
        
        stage1_result = {
            "discovered_urls_by_source": source_urls,
            "new_urls_by_source": new_urls_by_source,
            "new_urls": all_discovered_urls,
            "total_discovered": sum(len(urls) for urls in source_urls.values()),
            "total_new": len(all_discovered_urls),
            "processing_time_seconds": stage1_time,
            "sources_processed": len(sources),
            "sources_successful": len([s for s, urls in source_urls.items() if urls])
        }
        
        logger.info(
            "Stage 1 completed",
            cycle_id=self.current_cycle_id,
            total_discovered=stage1_result["total_discovered"],
            total_new=stage1_result["total_new"],
            processing_time_seconds=stage1_time,
            sources_successful=stage1_result["sources_successful"]
        )
        
        return stage1_result
    
    @performance_tracked("orchestrator.extract_urls")
    async def _extract_urls_from_all_sources(self, sources: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract URLs from all active sources using the content extractor.
        
        Args:
            sources: Dictionary of active sources
            
        Returns:
            Dictionary mapping source names to lists of extracted URLs
        """
        source_urls = {}
        source_items = list(sources.items())
        
        # Define extraction function for batch processing
        async def extract_from_source(source_item):
            source_id, source_config = source_item
            try:
                # Validate URL for security
                if not url_validator.is_valid_url(source_config.listing_url):
                    security_auditor.log_security_event(
                        event_type="INVALID_SOURCE_URL",
                        severity="MEDIUM",
                        description=f"Invalid source URL: {source_config.listing_url}",
                        url=source_config.listing_url
                    )
                    logger.warning(f"Invalid source URL for {source_id}: {source_config.listing_url}")
                    return source_id, []
                
                logger.info(f"Extracting URLs from source: {source_id}")
                urls = await self.content_extractor.extract_job_urls(
                    source_config.listing_url,
                    source_id
                )
                
                # Filter URLs through security validation
                safe_urls = [url for url in urls if url_validator.is_valid_url(url)]
                if len(safe_urls) < len(urls):
                    logger.warning(f"Filtered out {len(urls) - len(safe_urls)} unsafe URLs from {source_id}")
                
                logger.info(f"Extracted {len(safe_urls)} URLs from {source_id}")
                return source_id, safe_urls
                
            except Exception as e:
                logger.error(f"Failed to extract URLs from {source_id}: {str(e)}")
                return source_id, []
        
        # Process sources in batches with optimized concurrency
        results = await batch_processor.process_batch(
            source_items,
            extract_from_source,
            progress_callback=lambda done, total: logger.info(f"Source extraction progress: {done}/{total}")
        )
        
        # Convert results to dictionary
        for source_id, urls in results:
            if source_id is not None:  # Skip any failed extractions
                source_urls[source_id] = urls
        
        return source_urls
    
    @performance_tracked("orchestrator.stage2_analysis")
    async def run_stage2_analysis(self, job_urls: List[str]) -> Dict[str, Any]:
        """
        Stage 2: Analysis - Extract and structure job data from URLs.
        
        Args:
            job_urls: List of job URLs to process
            
        Returns:
            Dictionary with structured jobs and metrics
        """
        logger.info(
            "Starting Stage 2: Analysis", 
            cycle_id=self.current_cycle_id,
            urls_to_process=len(job_urls)
        )
        
        if not job_urls:
            logger.info("No new URLs to process in Stage 2")
            return {
                "structured_jobs": [],
                "jobs_processed": 0,
                "jobs_successful": 0,
                "processing_time_seconds": 0.0,
                "errors": []
            }
        
        stage2_start = time.time()
        
        # Process URLs in batches to manage memory and API limits
        batch_size = 10  # Process 10 jobs at a time
        all_structured_jobs = []
        all_errors = []
        
        for i in range(0, len(job_urls), batch_size):
            batch_urls = job_urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(job_urls) + batch_size - 1) // batch_size
            
            logger.info(
                "Processing batch",
                cycle_id=self.current_cycle_id,
                batch=f"{batch_num}/{total_batches}",
                batch_size=len(batch_urls)
            )
            
            batch_jobs = await self._process_job_batch(batch_urls)
            
            # Separate successful jobs from errors
            successful_jobs = [job for job in batch_jobs if job is not None]
            batch_errors = len(batch_urls) - len(successful_jobs)
            
            all_structured_jobs.extend(successful_jobs)
            if batch_errors > 0:
                all_errors.append(f"Batch {batch_num}: {batch_errors} failed extractions")
        
        # Save structured jobs to database
        if all_structured_jobs:
            # save_result = await self.database_service.upsert_jobs_batch(all_structured_jobs)  # Temporairement désactivé
            save_result = {"success": len(all_structured_jobs), "errors": 0}  # Mock pour les tests
            logger.info(
                "Jobs saved to database (MOCK)",
                cycle_id=self.current_cycle_id,
                saved=save_result.get("success", 0),
                errors=save_result.get("errors", 0)
            )
        
        stage2_time = time.time() - stage2_start
        
        stage2_result = {
            "structured_jobs": all_structured_jobs,
            "jobs_processed": len(job_urls),
            "jobs_successful": len(all_structured_jobs),
            "processing_time_seconds": stage2_time,
            "errors": all_errors,
            "database_save_result": save_result if all_structured_jobs else None
        }
        
        logger.info(
            "Stage 2 completed",
            cycle_id=self.current_cycle_id,
            jobs_processed=stage2_result["jobs_processed"],
            jobs_successful=stage2_result["jobs_successful"],
            processing_time_seconds=stage2_time,
            errors_count=len(all_errors)
        )
        
        return stage2_result
    
    @performance_tracked("orchestrator.process_job_batch")
    async def _process_job_batch(self, job_urls: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Process a batch of job URLs through Detail Scraper → Gemini pipeline.
        
        Args:
            job_urls: List of job URLs to process
            
        Returns:
            List of structured job data (None for failed extractions)
        """
        # Filter URLs through security validation
        safe_urls = []
        for url in job_urls:
            if url_validator.is_valid_url(url):
                safe_urls.append(url)
            else:
                security_auditor.log_security_event(
                    event_type="UNSAFE_JOB_URL",
                    severity="MEDIUM",
                    description=f"Unsafe job URL filtered: {url}",
                    url=url
                )
                logger.warning(f"Filtered unsafe job URL: {url}")
        
        if len(safe_urls) < len(job_urls):
            logger.warning(f"Filtered {len(job_urls) - len(safe_urls)} unsafe URLs from batch")
        
        # Step 1: Extract content using Detail Scraper
        jina_results = await self._extract_content_from_urls(safe_urls)
        
        # Step 2: Structure content using Gemini
        structured_results = await self._structure_extracted_content(safe_urls, jina_results)
        
        # Step 3: Sanitize structured data
        sanitized_results = []
        for result in structured_results:
            if result is not None:
                # Sanitize data for security
                sanitized_result = data_sanitizer.sanitize_job_data(result)
                sanitized_results.append(sanitized_result)
            else:
                sanitized_results.append(None)
        
        # Trigger plugin hooks for post-processing
        await plugin_registry.trigger_hook("post_process_job_batch", sanitized_results)
        
        return sanitized_results
    
    async def _extract_content_from_urls(self, job_urls: List[str]) -> List[Any]:
        """
        Extract content from job URLs using content extractor.
        
        Args:
            job_urls: List of job URLs to process
            
        Returns:
            List of extraction results (may include exceptions)
        """
        extraction_tasks = []
        for url in job_urls:
            source_site = self._determine_source_site(url)
            task = self.content_extractor.extract_content(url, source_site=source_site)
            extraction_tasks.append(task)
        
        # Execute content extractions concurrently
        return await asyncio.gather(*extraction_tasks, return_exceptions=True)
    
    async def _structure_extracted_content(
        self, 
        job_urls: List[str], 
        jina_results: List[Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Structure extracted content using Gemini AI.
        
        Args:
            job_urls: Original job URLs
            jina_results: Results from content extraction
            
        Returns:
            List of structured job data (None for failed extractions)
        """
        # Prepare Gemini tasks
        gemini_tasks = self._prepare_gemini_tasks(job_urls, jina_results)
        
        # Execute Gemini structuring
        return await self._execute_gemini_structuring(job_urls, gemini_tasks)
    
    def _prepare_gemini_tasks(self, job_urls: List[str], jina_results: List[Any]) -> List[Optional[Any]]:
        """
        Prepare Gemini structuring tasks from extraction results.
        
        Args:
            job_urls: Original job URLs
            jina_results: Results from content extraction
            
        Returns:
            List of Gemini tasks (None for invalid extractions)
        """
        gemini_tasks = []
        
        for i, result in enumerate(jina_results):
            if isinstance(result, Exception):
                logger.error(
                    "Jina extraction failed",
                    url=job_urls[i],
                    error=str(result)
                )
                gemini_tasks.append(None)
            elif result and result.get("content"):
                source_site = self._determine_source_site(job_urls[i])
                task = self.job_structurer.structure_job_data(
                    result["content"],
                    job_urls[i],
                    source_site
                )
                gemini_tasks.append(task)
            else:
                logger.warning("Empty content from Jina", url=job_urls[i])
                gemini_tasks.append(None)
        
        return gemini_tasks
    
    async def _execute_gemini_structuring(
        self, 
        job_urls: List[str], 
        gemini_tasks: List[Optional[Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Execute Gemini structuring tasks and handle errors.
        
        Args:
            job_urls: Original job URLs
            gemini_tasks: Prepared Gemini tasks
            
        Returns:
            List of structured job data (None for failed extractions)
        """
        structured_results = []
        
        for i, task in enumerate(gemini_tasks):
            if task is None:
                structured_results.append(None)
            else:
                try:
                    structured_data = await task
                    structured_results.append(structured_data)
                except Exception as e:
                    logger.error(
                        "Gemini structuring failed",
                        url=job_urls[i],
                        error=str(e)
                    )
                    structured_results.append(None)
        
        return structured_results
    
    def _determine_source_site(self, url: str) -> str:
        """
        Determine source site name from URL using SourceRegistry.
        
        Args:
            url: Job URL to analyze
            
        Returns:
            Source site identifier or "unknown" if not found
        """
        from urllib.parse import urlparse
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Get all sources from registry
            all_sources = SourceRegistry.get_all_sources()
            
            # Match domain against source configurations
            for source_id, source_config in all_sources.items():
                source_url = urlparse(source_config.listing_url)
                source_domain = source_url.netloc.lower()
                
                # Direct domain match
                if domain == source_domain:
                    return source_id
                
                # Subdomain match (e.g., tg.linkedin.com matches linkedin.com)
                if domain.endswith(f".{source_domain}") or source_domain.endswith(f".{domain}"):
                    return source_id
            
            # Fallback to legacy hardcoded mapping for edge cases
            domain_mapping = {
                "emploi.tg": "emploi_tg",
                "emploitogo.info": "emploitogo_info",
                "yop.l-frii.com": "yop_lfrii",
                "anpetogo.org": "anpetogo",
                "linkedin.com": "linkedin_togo",
                "tg.linkedin.com": "linkedin_togo",
                "indeed.com": "indeed_togo"
            }
            
            for domain_key, source_id in domain_mapping.items():
                if domain_key in domain:
                    return source_id
            
            logger.warning(f"Unknown source site for URL: {url}")
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error determining source site for URL {url}: {str(e)}")
            return "unknown"
    
    def _generate_cycle_result(
        self, 
        stage1_result: Dict[str, Any], 
        stage2_result: Dict[str, Any]
    ) -> ScrapingResult:
        """Generate final cycle result with combined metrics."""
        total_time = time.time() - self.cycle_start_time
        
        # Combine errors from both stages
        all_errors = []
        if stage2_result.get("errors"):
            all_errors.extend(stage2_result["errors"])
        
        # Determine overall success
        success = (
            stage1_result["sources_successful"] > 0 and
            stage2_result["jobs_successful"] > 0 and
            len(all_errors) == 0
        )
        
        return ScrapingResult(
            success=success,
            jobs_found=stage1_result["total_new"],
            jobs_processed=stage2_result["jobs_successful"],
            errors=all_errors,
            processing_time_seconds=total_time,
            source_site="all_sources"
        )
    
    async def _update_scraping_stats(self, cycle_result: ScrapingResult):
        """Update scraping statistics in database."""
        try:
            stats_data = {
                "source_site": "orchestrator",
                "scrape_date": date.today(),
                "urls_discovered": cycle_result.jobs_found,
                "urls_processed": cycle_result.jobs_found,
                "jobs_created": cycle_result.jobs_processed,
                "jobs_updated": 0,  # We don't track updates separately yet
                "success_rate": (cycle_result.jobs_processed / cycle_result.jobs_found * 100) if cycle_result.jobs_found > 0 else 0,
                "processing_time_seconds": int(cycle_result.processing_time_seconds),
                "errors_count": len(cycle_result.errors),
                "error_details": {"errors": cycle_result.errors} if cycle_result.errors else None
            }
            
            # await self.database_service.update_scraping_stats(stats_data)  # Temporairement désactivé
            logger.info("Scraping stats update skipped (database service disabled)")
            
        except Exception as e:
            logger.error("Failed to update scraping stats", error=str(e))
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the orchestrator."""
        return {
            "performance_metrics": performance_monitor.get_all_stats(),
            "slow_operations": performance_monitor.get_slow_operations(),
            "security_summary": security_auditor.get_security_summary(),
            "plugin_status": plugin_registry.list_plugins()
        }
    
    async def trigger_plugin_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger a plugin hook."""
        return await plugin_registry.trigger_hook(hook_name, *args, **kwargs)