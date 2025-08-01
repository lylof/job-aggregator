"""
Enhanced Pipeline Orchestrator for Phase 2.
Orchestrates the complete Stage 2 enhanced data extraction pipeline.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from ..config import SourceRegistry
from ..models_enriched import EnrichedJobData, EnhancedPipelineResult
from .enhanced_detail_scraper import EnhancedDetailScraper
from .listing_scraper import ListingScraper
from .database_service import DatabaseService

logger = structlog.get_logger(__name__)

class EnhancedPipelineOrchestrator:
    """
    Orchestrates the complete Phase 2 enhanced pipeline:
    1. URL discovery (Stage 1)
    2. Enhanced data extraction (Stage 2)
    3. Quality assessment and storage
    4. Performance monitoring
    """
    
    def __init__(
        self,
        listing_scraper: Optional[ListingScraper] = None,
        enhanced_scraper: Optional[EnhancedDetailScraper] = None,
        database_service: Optional[DatabaseService] = None
    ):
        """
        Initialize the Enhanced Pipeline Orchestrator.
        
        Args:
            listing_scraper: Optional ListingScraper instance
            enhanced_scraper: Optional EnhancedDetailScraper instance
            database_service: Optional DatabaseService instance
        """
        self.listing_scraper = listing_scraper or ListingScraper()
        self.enhanced_scraper = enhanced_scraper or EnhancedDetailScraper()
        self.database_service = database_service or DatabaseService()
        self.source_registry = SourceRegistry()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.enhanced_scraper, '__aexit__'):
            await self.enhanced_scraper.__aexit__(exc_type, exc_val, exc_tb)
    
    async def run_enhanced_pipeline(
        self,
        source_name: str,
        max_pages: Optional[int] = None,
        max_concurrent_extractions: int = 5
    ) -> EnhancedPipelineResult:
        """
        Run the complete enhanced pipeline for a source.
        
        Args:
            source_name: Name of the source to process
            max_pages: Maximum pages to scrape (None for source default)
            max_concurrent_extractions: Max concurrent Stage 2 extractions
            
        Returns:
            EnhancedPipelineResult with metrics and enriched jobs
        """
        pipeline_start = time.time()
        correlation_id = self._generate_correlation_id(source_name)
        
        logger.info("Starting enhanced pipeline execution",
                   source=source_name,
                   max_pages=max_pages,
                   max_concurrent=max_concurrent_extractions,
                   correlation_id=correlation_id)
        
        try:
            # 1. Validate source configuration
            source_config = self.source_registry.get_source(source_name)
            if not source_config:
                logger.error("Source configuration not found",
                           source=source_name,
                           correlation_id=correlation_id)
                return self._create_failed_result("Source configuration not found")
            
            # Check if Stage 2 is enabled
            if not source_config.is_stage2_enabled():
                logger.info("Stage 2 not enabled for source, running Stage 1 only",
                          source=source_name,
                          correlation_id=correlation_id)
                return await self._run_stage1_only(source_name, max_pages, correlation_id)
            
            # 2. Stage 1: URL Discovery
            stage1_start = time.time()
            job_urls = await self._discover_job_urls(source_name, max_pages, correlation_id)
            stage1_duration = time.time() - stage1_start
            
            if not job_urls:
                logger.warning("No job URLs discovered in Stage 1",
                             source=source_name,
                             correlation_id=correlation_id)
                return self._create_failed_result("No job URLs discovered")
            
            logger.info("Stage 1 URL discovery completed",
                       source=source_name,
                       urls_found=len(job_urls),
                       duration_seconds=round(stage1_duration, 2),
                       correlation_id=correlation_id)
            
            # 3. Stage 2: Enhanced Data Extraction
            stage2_start = time.time()
            enriched_jobs = await self.enhanced_scraper.extract_multiple_enriched_jobs(
                job_urls, source_name, max_concurrent_extractions
            )
            stage2_duration = time.time() - stage2_start
            
            logger.info("Stage 2 enhanced extraction completed",
                       source=source_name,
                       successful_extractions=len(enriched_jobs),
                       total_urls=len(job_urls),
                       duration_seconds=round(stage2_duration, 2),
                       correlation_id=correlation_id)
            
            # 4. Quality Assessment and Storage
            storage_start = time.time()
            stored_count = await self._store_enriched_jobs(enriched_jobs, correlation_id)
            storage_duration = time.time() - storage_start
            
            # 5. Create result with comprehensive metrics
            total_duration = time.time() - pipeline_start
            
            pipeline_metrics = {
                "source_name": source_name,
                "stage1_duration_seconds": round(stage1_duration, 2),
                "stage2_duration_seconds": round(stage2_duration, 2),
                "storage_duration_seconds": round(storage_duration, 2),
                "total_duration_seconds": round(total_duration, 2),
                "urls_discovered": len(job_urls),
                "successful_extractions": len(enriched_jobs),
                "failed_extractions": len(job_urls) - len(enriched_jobs),
                "success_rate": len(enriched_jobs) / len(job_urls) if job_urls else 0,
                "stored_jobs": stored_count,
                "correlation_id": correlation_id
            }
            
            result = EnhancedPipelineResult(
                enriched_jobs=enriched_jobs,
                pipeline_metrics=pipeline_metrics,
                success=True,
                total_duration_seconds=total_duration,
                total_urls_processed=len(job_urls),
                failed_extractions=len(job_urls) - len(enriched_jobs)
            )
            
            logger.info("Enhanced pipeline execution completed successfully",
                       source=source_name,
                       total_duration=round(total_duration, 2),
                       success_rate=f"{result.success_rate:.2%}",
                       avg_quality_score=round(result.average_quality_score, 2),
                       correlation_id=correlation_id)
            
            return result
            
        except Exception as e:
            total_duration = time.time() - pipeline_start
            logger.error("Enhanced pipeline execution failed",
                        source=source_name,
                        error=str(e),
                        duration_seconds=round(total_duration, 2),
                        correlation_id=correlation_id)
            return self._create_failed_result(f"Pipeline execution failed: {str(e)}")
    
    async def run_enhanced_pipeline_batch(
        self,
        source_names: List[str],
        max_pages_per_source: Optional[int] = None,
        max_concurrent_sources: int = 3
    ) -> Dict[str, EnhancedPipelineResult]:
        """
        Run enhanced pipeline for multiple sources concurrently.
        
        Args:
            source_names: List of source names to process
            max_pages_per_source: Max pages per source
            max_concurrent_sources: Max concurrent source processing
            
        Returns:
            Dictionary mapping source names to their results
        """
        logger.info("Starting batch enhanced pipeline execution",
                   sources=source_names,
                   max_concurrent_sources=max_concurrent_sources)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent_sources)
        
        async def run_source_with_semaphore(source_name: str) -> tuple[str, EnhancedPipelineResult]:
            async with semaphore:
                result = await self.run_enhanced_pipeline(source_name, max_pages_per_source)
                return source_name, result
        
        # Execute all sources concurrently
        tasks = [run_source_with_semaphore(source) for source in source_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        batch_results = {}
        for result in results:
            if isinstance(result, tuple):
                source_name, pipeline_result = result
                batch_results[source_name] = pipeline_result
            elif isinstance(result, Exception):
                logger.error("Batch source processing failed", error=str(result))
        
        # Log batch summary
        successful_sources = sum(1 for r in batch_results.values() if r.success)
        total_jobs = sum(r.successful_extractions for r in batch_results.values())
        
        logger.info("Batch enhanced pipeline execution completed",
                   successful_sources=successful_sources,
                   total_sources=len(source_names),
                   total_enriched_jobs=total_jobs)
        
        return batch_results
    
    async def _discover_job_urls(
        self,
        source_name: str,
        max_pages: Optional[int],
        correlation_id: str
    ) -> List[str]:
        """
        Discover job URLs using Stage 1 listing scraper.
        
        Args:
            source_name: Source name
            max_pages: Maximum pages to scrape
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of discovered job URLs
        """
        try:
            # Use existing listing scraper for URL discovery
            urls = await self.listing_scraper.scrape_job_urls(source_name, max_pages)
            
            logger.debug("URL discovery completed",
                        source=source_name,
                        urls_found=len(urls),
                        correlation_id=correlation_id)
            
            return urls
            
        except Exception as e:
            logger.error("URL discovery failed",
                        source=source_name,
                        error=str(e),
                        correlation_id=correlation_id)
            return []
    
    async def _store_enriched_jobs(
        self,
        enriched_jobs: List[EnrichedJobData],
        correlation_id: str
    ) -> int:
        """
        Store enriched jobs in database.
        
        Args:
            enriched_jobs: List of enriched job data
            correlation_id: Correlation ID for tracking
            
        Returns:
            Number of successfully stored jobs
        """
        if not enriched_jobs:
            return 0
        
        try:
            stored_count = 0
            for job in enriched_jobs:
                try:
                    # Convert to database format and store
                    job_dict = job.to_dict()
                    await self.database_service.store_enriched_job(job_dict)
                    stored_count += 1
                except Exception as e:
                    logger.error("Failed to store individual job",
                               job_id=job.job_id,
                               error=str(e),
                               correlation_id=correlation_id)
            
            logger.info("Enriched jobs storage completed",
                       stored=stored_count,
                       total=len(enriched_jobs),
                       correlation_id=correlation_id)
            
            return stored_count
            
        except Exception as e:
            logger.error("Batch job storage failed",
                        error=str(e),
                        correlation_id=correlation_id)
            return 0
    
    async def _run_stage1_only(
        self,
        source_name: str,
        max_pages: Optional[int],
        correlation_id: str
    ) -> EnhancedPipelineResult:
        """
        Run Stage 1 only pipeline for sources without Stage 2 enabled.
        
        Args:
            source_name: Source name
            max_pages: Maximum pages
            correlation_id: Correlation ID
            
        Returns:
            Pipeline result with Stage 1 data only
        """
        start_time = time.time()
        
        # Discover URLs
        job_urls = await self._discover_job_urls(source_name, max_pages, correlation_id)
        
        # For Stage 1 only, we don't do enhanced extraction
        total_duration = time.time() - start_time
        
        pipeline_metrics = {
            "source_name": source_name,
            "stage1_duration_seconds": round(total_duration, 2),
            "stage2_duration_seconds": 0,
            "urls_discovered": len(job_urls),
            "stage2_enabled": False,
            "correlation_id": correlation_id
        }
        
        return EnhancedPipelineResult(
            enriched_jobs=[],
            pipeline_metrics=pipeline_metrics,
            success=len(job_urls) > 0,
            total_duration_seconds=total_duration,
            total_urls_processed=len(job_urls)
        )
    
    def _create_failed_result(self, error_message: str) -> EnhancedPipelineResult:
        """Create a failed pipeline result."""
        return EnhancedPipelineResult(
            enriched_jobs=[],
            pipeline_metrics={"error": error_message},
            success=False,
            total_duration_seconds=0
        )
    
    def _generate_correlation_id(self, source_name: str) -> str:
        """Generate correlation ID for pipeline tracking."""
        import hashlib
        timestamp = str(int(time.time()))
        return hashlib.md5(f"{source_name}_{timestamp}".encode()).hexdigest()[:12]
    
    async def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline statistics.
        
        Returns:
            Dictionary with pipeline performance metrics
        """
        try:
            # This would typically query the database for historical metrics
            stats = {
                "total_sources_configured": len(self.source_registry.get_all_sources()),
                "stage2_enabled_sources": len([
                    s for s in self.source_registry.get_all_sources().values()
                    if s.is_stage2_enabled()
                ]),
                "pipeline_version": "2.1",
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get pipeline statistics", error=str(e))
            return {"error": str(e)}