"""
JinaScraper Application - Enhanced version with modern CLI interface.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import structlog

from .core.orchestrator import ScrapingOrchestrator
from .models import ScrapingResult
from .utils.enhanced_logger import create_logger
from .utils.display_manager import DisplayManager, DisplayConfig, create_simple_display, create_verbose_display, create_compact_display
from .utils.report_generator import ReportData


logger = structlog.get_logger(__name__)


@dataclass
class ScrapeOptions:
    """Configuration options for scraping operations."""
    sources: Optional[List[str]] = None  # --sources
    max_urls: int = 100                  # --max-urls
    dry_run: bool = False               # --dry-run
    verbose: bool = False               # --verbose
    quiet: bool = False                 # --quiet
    show_urls: int = 3                  # --show-urls
    use_colors: bool = True             # --no-color (inverted)
    compact_mode: bool = False          # --compact


@dataclass
class ScrapeResults:
    """Results from a scraping operation."""
    success: bool
    jobs_processed: int
    sources_processed: int
    processing_time_seconds: float
    errors: List[str]
    scraping_result: Optional[ScrapingResult] = None
    cache_hit_rate: float = 0.0
    total_urls_found: int = 0
    source_details: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.source_details is None:
            self.source_details = []


class JinaScraperAppEnhanced:
    """
    Enhanced JinaScraper application with modern CLI interface.
    
    This version uses the new DisplayManager for a professional,
    visually appealing command-line experience.
    """
    
    def __init__(self):
        """Initialize the enhanced JinaScraper application."""
        self.orchestrator = None
        self.display_manager = None
        self.enhanced_logger = None
        logger.info("JinaScraperAppEnhanced initialized")
    
    def _create_display_manager(self, options: ScrapeOptions) -> DisplayManager:
        """
        Create appropriate display manager based on options.
        
        Args:
            options: Scraping options
            
        Returns:
            Configured DisplayManager instance
        """
        if options.quiet:
            return create_simple_display(use_colors=options.use_colors, quiet=True)
        elif options.verbose:
            return create_verbose_display(use_colors=options.use_colors)
        elif options.compact_mode:
            return create_compact_display(use_colors=options.use_colors)
        else:
            return create_simple_display(use_colors=options.use_colors, quiet=False)
    
    async def run_full_scrape(self, options: ScrapeOptions) -> ScrapeResults:
        """
        Execute a full scraping cycle with enhanced visual interface.
        
        Args:
            options: Configuration options for the scraping operation
            
        Returns:
            ScrapeResults containing the outcome and metrics
        """
        start_time = time.time()
        errors = []
        
        # Create display manager
        self.display_manager = self._create_display_manager(options)
        
        # Initialize enhanced logger (fallback for compatibility)
        self.enhanced_logger = create_logger(
            verbose=options.verbose,
            quiet=options.quiet,
            use_colors=options.use_colors,
            show_urls=options.show_urls
        )
        
        try:
            # Start display manager
            async with self.display_manager.display_context():
                
                # Initialize orchestrator with async context manager
                async with ScrapingOrchestrator() as orchestrator:
                    self.orchestrator = orchestrator
                    
                    # Set up orchestrator callbacks for display updates
                    orchestrator.set_display_callback(self._on_orchestrator_update)
                    
                    # Pass enhanced logger to orchestrator (compatibility)
                    if hasattr(orchestrator, 'set_enhanced_logger'):
                        orchestrator.set_enhanced_logger(self.enhanced_logger)
                    
                    # Configure orchestrator based on options
                    if options.sources:
                        self.display_manager.add_message(
                            f"Filtrage des sources: {options.sources}", 
                            "info", 
                            "configuration"
                        )
                    
                    if options.dry_run:
                        self.display_manager.add_message(
                            "Mode dry-run activé - aucune donnée ne sera sauvegardée", 
                            "info", 
                            "configuration"
                        )
                    
                    # Execute Stage 1: Exploration
                    self.display_manager.set_stage("ÉTAPE 1", "EXPLORATION DES SOURCES")
                    
                    # Simulate stage 1 progress (this would be integrated with actual orchestrator)
                    await self._simulate_stage1_progress()
                    
                    # Execute Stage 2: Analysis
                    self.display_manager.set_stage("ÉTAPE 2", "ANALYSE ET ENRICHISSEMENT")
                    
                    # Execute the actual scraping cycle
                    scraping_result = await orchestrator.run_full_cycle()
                    
                    # Calculate processing time
                    processing_time = time.time() - start_time
                    
                    # Build enhanced results
                    results = await self._build_enhanced_results(
                        scraping_result, options, processing_time, errors
                    )
                    
                    # Show final report using new display manager
                    await self._show_final_report(results)
                    
                    return results
                    
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            
            if self.display_manager:
                self.display_manager.add_message(error_msg, "error", "system")
            
            return ScrapeResults(
                success=False,
                jobs_processed=0,
                sources_processed=0,
                processing_time_seconds=time.time() - start_time,
                errors=errors
            )
    
    async def _simulate_stage1_progress(self):
        """
        Simulate Stage 1 progress for demonstration.
        This would be replaced by actual orchestrator integration.
        """
        sources = [
            ("Emploi.tg", 25, True),
            ("ANPE Togo", 15, True),
            ("EmploiTogo.info", 64, True),
            ("YOP L-FRII", 35, True),
            ("LinkedIn Togo", 0, False),  # Will timeout
            ("Indeed Togo", 0, False)    # Will error
        ]
        
        # Initialize all sources
        for source_name, target_urls, will_succeed in sources:
            self.display_manager.update_source_progress(
                source_name=source_name,
                progress=0,
                total=100,
                status="running",
                urls_found=0
            )
        
        # Simulate progress
        for step in range(0, 101, 10):
            for source_name, target_urls, will_succeed in sources:
                if not will_succeed:
                    if source_name == "LinkedIn Togo" and step > 30:
                        self.display_manager.update_source_progress(
                            source_name=source_name,
                            progress=30,
                            total=100,
                            status="timeout",
                            urls_found=0
                        )
                        if step == 40:  # Only add message once
                            self.display_manager.add_message(
                                "Connection timeout after 30s", 
                                "warning", 
                                source_name
                            )
                    elif source_name == "Indeed Togo" and step > 10:
                        self.display_manager.update_source_progress(
                            source_name=source_name,
                            progress=10,
                            total=100,
                            status="error",
                            urls_found=0,
                            error_message="HTTP 400 Error"
                        )
                        if step == 20:  # Only add message once
                            self.display_manager.add_message(
                                "HTTP 400 Bad Request", 
                                "error", 
                                source_name
                            )
                else:
                    # Successful sources
                    urls_found = int((step / 100) * target_urls)
                    status = "completed" if step == 100 else "running"
                    
                    self.display_manager.update_source_progress(
                        source_name=source_name,
                        progress=step,
                        total=100,
                        status=status,
                        urls_found=urls_found
                    )
            
            # Update global metrics
            total_cache_hits = step * 2
            self.display_manager.update_global_metrics({
                'cache_hits': total_cache_hits,
                'api_savings': total_cache_hits // 3,
                'total_urls_discovered': step * 3
            })
            
            await asyncio.sleep(0.1)
    
    def _on_orchestrator_update(self, event_type: str, data: Dict[str, Any]):
        """
        Callback for orchestrator updates.
        
        Args:
            event_type: Type of update event
            data: Event data
        """
        if not self.display_manager:
            return
        
        if event_type == "source_progress":
            self.display_manager.update_source_progress(
                source_name=data.get("source_name"),
                progress=data.get("progress", 0),
                total=data.get("total", 100),
                status=data.get("status", "running"),
                urls_found=data.get("urls_found", 0)
            )
        
        elif event_type == "stage_change":
            self.display_manager.set_stage(
                data.get("stage", ""),
                data.get("description", "")
            )
        
        elif event_type == "error":
            self.display_manager.add_message(
                data.get("message", "Unknown error"),
                "error",
                data.get("source", "system")
            )
        
        elif event_type == "warning":
            self.display_manager.add_message(
                data.get("message", "Unknown warning"),
                "warning",
                data.get("source", "system")
            )
        
        elif event_type == "info":
            self.display_manager.add_message(
                data.get("message", ""),
                "info",
                data.get("source", "system")
            )
        
        elif event_type == "metrics_update":
            self.display_manager.update_global_metrics(data)
    
    async def _build_enhanced_results(self, scraping_result: ScrapingResult, 
                                    options: ScrapeOptions, processing_time: float, 
                                    errors: List[str]) -> ScrapeResults:
        """
        Build enhanced results with additional metrics.
        
        Args:
            scraping_result: Core scraping result
            options: Scraping options
            processing_time: Total processing time
            errors: List of errors
            
        Returns:
            Enhanced ScrapeResults
        """
        # Calculate additional metrics
        cache_hit_rate = 0.75  # This would come from actual cache manager
        total_urls_found = scraping_result.jobs_found if scraping_result else 0
        
        # Build source details
        source_details = [
            {'name': 'Emploi.tg', 'jobs_processed': 25},
            {'name': 'ANPE Togo', 'jobs_processed': 15},
            {'name': 'EmploiTogo.info', 'jobs_processed': 64},
            {'name': 'YOP L-FRII', 'jobs_processed': 35}
        ]
        
        return ScrapeResults(
            success=scraping_result.success if scraping_result else False,
          
      jobs_processed=scraping_result.jobs_processed if scraping_result else 0,
            sources_processed=len(options.sources) if options.sources else 6,
            processing_time_seconds=processing_time,
            errors=errors,
            scraping_result=scraping_result,
            cache_hit_rate=cache_hit_rate,
            total_urls_found=total_urls_found,
            source_details=source_details
        )
    
    async def _show_final_report(self, results: ScrapeResults):
        """
        Show the final report using the display manager.
        
        Args:
            results: Scraping results
        """
        # Convert to ReportData format
        report_data = ReportData(
            total_sources=6,  # Total configured sources
            successful_sources=results.sources_processed,
            total_urls_found=results.total_urls_found,
            total_jobs_processed=results.jobs_processed,
            cache_hit_rate=results.cache_hit_rate,
            processing_time=results.processing_time_seconds,
            errors=[{'type': 'error', 'message': error, 'source': 'system'} for error in results.errors],
            warnings=[],
            performance_metrics={'avg_processing_time': results.processing_time_seconds / max(results.jobs_processed, 1)},
            source_details=results.source_details
        )
        
        # Show the final report
        self.display_manager.show_final_report(report_data)
    
    def generate_scrape_report(self, results: ScrapeResults, options: ScrapeOptions) -> bool:
        """
        Generate and display a scraping report (compatibility method).
        
        Args:
            results: Results from the scraping operation
            options: Original scraping options
            
        Returns:
            bool: True if report generation succeeded
        """
        try:
            # Use the enhanced display manager if available
            if self.display_manager:
                report_data = ReportData(
                    total_sources=6,
                    successful_sources=results.sources_processed,
                    total_urls_found=results.total_urls_found,
                    total_jobs_processed=results.jobs_processed,
                    cache_hit_rate=results.cache_hit_rate,
                    processing_time=results.processing_time_seconds,
                    errors=[{'type': 'error', 'message': error, 'source': 'system'} for error in results.errors],
                    warnings=[],
                    performance_metrics={'avg_processing_time': results.processing_time_seconds / max(results.jobs_processed, 1)},
                    source_details=results.source_details
                )
                
                self.display_manager.show_final_report(report_data)
                return True
            
            # Fallback to basic report (from original app.py)
            print("\n" + "="*60)
            print("🔍 JINASCRAPER REPORT")
            print("="*60)
            
            # Basic metrics
            print(f"✅ Status: {'SUCCESS' if results.success else 'FAILED'}")
            print(f"📊 Jobs Processed: {results.jobs_processed}")
            print(f"🌐 Sources Processed: {results.sources_processed}")
            print(f"⏱️  Processing Time: {results.processing_time_seconds:.2f}s")
            
            # Options used
            print(f"\n📋 Configuration:")
            print(f"   Sources Filter: {options.sources or 'All'}")
            print(f"   Max URLs: {options.max_urls}")
            print(f"   Dry Run: {options.dry_run}")
            print(f"   Verbose: {options.verbose}")
            
            # Detailed results if available
            if results.scraping_result:
                sr = results.scraping_result
                print(f"\n📈 Detailed Metrics:")
                print(f"   Success Rate: {(sr.jobs_processed / max(sr.jobs_found, 1)) * 100:.1f}%")
                print(f"   Jobs Found: {sr.jobs_found}")
                print(f"   Processing Time: {sr.processing_time_seconds:.2f}s")
                print(f"   Source Site: {sr.source_site}")
                print(f"   Timestamp: {sr.timestamp}")
            
            # Errors if any
            if results.errors:
                print(f"\n❌ Errors ({len(results.errors)}):")
                for error in results.errors:
                    print(f"   - {error}")
            
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return False


# Convenience function to create the enhanced app
def create_enhanced_app() -> JinaScraperAppEnhanced:
    """
    Create an enhanced JinaScraper application instance.
    
    Returns:
        JinaScraperAppEnhanced instance
    """
    return JinaScraperAppEnhanced()


# Backward compatibility - alias to original app class
JinaScraperApp = JinaScraperAppEnhanced