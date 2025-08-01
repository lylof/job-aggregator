"""Listing Scraper for extracting job URLs from listing pages (Stage 1)."""

import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import structlog

from ..config import SourceRegistry, JINA_BASE_CONFIG, SourceBaseConfig
from .jina_client import JinaClient
from .url_cleaner import clean_urls_by_source, clean_url


logger = structlog.get_logger(__name__)


class ListingScraper:
    """Service for extracting job URLs from listing pages (Stage 1)."""
    
    def __init__(self, jina_client: Optional[JinaClient] = None):
        """
        Initialize the ListingScraper.
        
        Args:
            jina_client: Optional JinaClient instance. If not provided, a new one will be created.
        """
        self.jina_client = jina_client or JinaClient()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not isinstance(self.jina_client, JinaClient):
            self.jina_client = await self.jina_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.jina_client:
            await self.jina_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_job_urls(
        self, 
        listing_url: str, 
        source_name: Optional[str] = None,
        css_selector: Optional[str] = None
    ) -> List[str]:
        """
        Extract job posting URLs from a job listing page using Jina Reader.
        Optimized for Stage 1 (Exploration) with gather_all_links_at_the_end=true.
        
        Args:
            listing_url: URL of the job listing page
            source_name: Name of the source (for site-specific configuration)
            css_selector: Optional CSS selector to focus on job listings
            
        Returns:
            List of job posting URLs found on the page
        """
        try:
            logger.info("Extracting job URLs from listing", url=listing_url, source=source_name)
            
            # Get source-specific configuration
            source_config = None
            if source_name:
                source_config = SourceRegistry.get_source(source_name)
            
            # Stage 1 optimized parameters for Jina Reader
            params = {
                "gather_all_links_at_the_end": "true",
                "remove_all_images": "true",
                "timeout": "30"
            }
            
            # Use source-specific CSS selector or provided one
            selector = css_selector
            if source_config and source_config.css_selector_jobs:
                selector = source_config.css_selector_jobs
            
            if selector:
                params["css_selector_only"] = selector
                logger.info("Using CSS selector for job extraction", selector=selector, source=source_name)
            
            # Use Jina Reader with Stage 1 configuration
            response_data = await self.jina_client.make_request(listing_url, params)
            content = response_data.get("content", "")
            
            if not content:
                logger.warning("No content extracted from listing page", url=listing_url)
                return []
            
            # Extract URLs from the "Buttons & Links" section created by Jina Reader
            urls = self._extract_job_urls_from_jina_content(content, listing_url, source_config)
            
            logger.info(
                "Job URLs extracted from listing",
                listing_url=listing_url,
                urls_found=len(urls),
                css_selector=selector,
                source=source_name
            )
            
            return urls
            
        except Exception as e:
            logger.error(
                "Failed to extract job URLs",
                listing_url=listing_url,
                error=str(e)
            )
            raise
    
    def _extract_job_urls_from_jina_content(
        self, 
        content: str, 
        base_url: str, 
        source_config = None
    ) -> List[str]:
        """
        Extract job URLs from Jina Reader content with "Buttons & Links" section.
        
        Jina Reader with gather_all_links_at_the_end=true creates a section
        at the end with all links found on the page.
        """
        # Déterminer le nom de la source à partir de l'URL de base
        source_name = None
        if source_config:
            # Si la configuration est fournie, utiliser son nom
            source_name = source_config.name.lower().replace(' ', '_')
        elif "anpetogo.org" in base_url:
            # Détection automatique pour ANPE
            source_name = "anpe_togo"
        
        # Look for the "Buttons & Links" section created by Jina Reader
        links_section_pattern = r'(?:Buttons?\s*&?\s*Links?|Links?\s*&?\s*Buttons?)\s*:?\s*\n(.*?)(?:\n\n|\Z)'
        links_match = re.search(links_section_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if links_match:
            links_content = links_match.group(1)
            logger.info("Found Buttons & Links section in Jina content")
        else:
            # Fallback to full content if no links section found
            links_content = content
            logger.info("No Buttons & Links section found, using full content")
        
        # Patterns spécifiques pour ANPE Togo
        if source_name == "anpe_togo":
            job_url_patterns = [
                r'(https://anpetogo\.org/job/[^\s<>"\']+)'  # Pattern spécifique ANPE
            ]
        else:
            # Extract URLs that look like job postings (patterns génériques)
            job_url_patterns = [
                r'https?://[^\s<>"\']+(?:job|emploi|offre|poste|career|vacancy)[^\s<>"\']*',
                r'https?://[^\s<>"\']+/(?:jobs?|emplois?|offres?|postes?|careers?|vacancies?)[^\s<>"\']*',
                r'https?://[^\s<>"\']+[?&](?:job|emploi|offre)(?:_?id|Id)?=\d+[^\s<>"\']*'
            ]
        
        # Extraire toutes les URLs selon les patterns
        all_urls = []
        for pattern in job_url_patterns:
            urls = re.findall(pattern, links_content, re.IGNORECASE)
            all_urls.extend(urls)
        
        # Nettoyer et valider les URLs selon la source
        if source_name:
            valid_urls = clean_urls_by_source(all_urls, source_name)
        else:
            # Nettoyage générique si la source n'est pas identifiée
            valid_urls = []
            base_domain = urlparse(base_url).netloc
            
            for url in all_urls:
                try:
                    # Clean URL
                    url = clean_url(url)
                    
                    parsed = urlparse(url)
                    if parsed.netloc and parsed.scheme in ('http', 'https'):
                        # Filter out obvious non-job URLs
                        if not self._is_likely_job_url(url, base_domain):
                            continue
                        valid_urls.append(url)
                except Exception:
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in valid_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _is_likely_job_url(self, url: str, base_domain: str) -> bool:
        """
        Determine if a URL is likely to be a job posting.
        
        Args:
            url: URL to check
            base_domain: Base domain of the listing page
            
        Returns:
            True if URL is likely a job posting
        """
        url_lower = url.lower()
        parsed = urlparse(url)
        
        # Skip URLs that are clearly not job postings
        skip_patterns = [
            'facebook.com', 'twitter.com', 'linkedin.com/in/', 'instagram.com',
            'youtube.com', 'google.com', 'mailto:', 'tel:', 'javascript:',
            '/login', '/register', '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.doc', '.jpg', '.png', '.gif', '.css', '.js', '.ico',
            'favicon', 'logo', 'image', 'photo', 'recherche-jobs-togo?f%5B',
            'utm_source=', 'utm_medium=', 'utm_campaign=', '?page=', '&page=',
            '/themes/', '/sites/', '/modules/', '/misc/', '/files/'
        ]
        
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Must be from the same domain for emploi.tg
        if base_domain == 'www.emploi.tg' and parsed.netloc != base_domain:
            return False
        
        # For emploi.tg, look for specific job URL patterns
        if 'emploi.tg' in parsed.netloc:
            # Job URLs on emploi.tg typically have patterns like:
            # /offre-emploi-togo/[job-title]-[id]
            job_url_patterns = [
                '/offre-emploi-togo/', '/offre-emploi/', '/node/', '/emploi/', '/job/'
            ]
            
            path = parsed.path.lower()
            for pattern in job_url_patterns:
                if pattern in path:
                    # Additional check: should have numeric ID at the end
                    if re.search(r'-\d+$', path) or re.search(r'/\d+$', path):
                        return True
            
            return False
        
        # For other domains, use general job keywords
        job_keywords = [
            'job', 'emploi', 'offre', 'poste', 'career', 'vacancy',
            'recrutement', 'candidature', 'application'
        ]
        
        for keyword in job_keywords:
            if keyword in url_lower:
                return True
        
        return False
    
    async def extract_urls_from_all_sources(self, sources_filter: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Extract job URLs from all configured Togo sources or filtered sources in parallel.
        
        Args:
            sources_filter: Optional list of source names to process.
                          If None, processes all active sources.
        
        Returns:
            Dictionary mapping source names to lists of job URLs
        """
        logger.info("Starting parallel URL extraction from sources", sources_filter=sources_filter)
        
        sources = SourceRegistry.get_active_sources()
        
        # ✅ CORRECTION: Apply source filtering
        if sources_filter:
            # Filter sources according to the provided list
            filtered_sources = {
                name: config for name, config in sources.items() 
                if name in sources_filter
            }
            
            # Check that all requested sources exist
            missing_sources = set(sources_filter) - set(sources.keys())
            if missing_sources:
                logger.warning(
                    "Some requested sources not found in active sources",
                    missing_sources=list(missing_sources),
                    available_sources=list(sources.keys())
                )
            
            sources = filtered_sources
            logger.info(
                f"Source filtering applied: {len(sources)} sources selected out of {len(SourceRegistry.get_active_sources())}",
                selected_sources=list(sources.keys())
            )
        else:
            logger.info(f"No filtering applied: processing all {len(sources)} active sources")
        
        if not sources:
            logger.warning("No sources to process after filtering")
            return {}
        
        tasks = []
        
        for source_name, source_config in sources.items():
            task = self._extract_urls_from_source(source_name, source_config)
            tasks.append(task)
        
        # Execute all source extractions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        source_urls = {}
        total_urls = 0
        
        for i, (source_name, _) in enumerate(sources.items()):
            result = results[i]
            
            if isinstance(result, Exception):
                logger.error(
                    "Source extraction failed",
                    source=source_name,
                    error=str(result)
                )
                source_urls[source_name] = []
            else:
                source_urls[source_name] = result
                total_urls += len(result)
                logger.info(
                    "Source extraction completed",
                    source=source_name,
                    urls_found=len(result)
                )
        
        logger.info(
            "Parallel URL extraction completed",
            total_sources=len(sources),
            total_urls=total_urls,
            successful_sources=sum(1 for urls in source_urls.values() if urls)
        )
        
        return source_urls
    
    async def _extract_urls_from_source(
        self, 
        source_name: str, 
        source_config: SourceBaseConfig
    ) -> List[str]:
        """
        Extract URLs from a single source with source-specific configuration.
        
        Args:
            source_name: Name of the source
            source_config: Configuration for the source
            
        Returns:
            List of job URLs from this source
        """
        try:
            logger.info(
                "Extracting URLs from source",
                source=source_name,
                url=source_config.listing_url
            )
            
            # Apply source-specific delay
            if source_config.request_delay > 0:
                await asyncio.sleep(source_config.request_delay)
            
            # Extract URLs from the main listing page
            urls = await self.extract_job_urls(
                source_config.listing_url,
                source_name=source_name
            )
            
            # Handle pagination if configured
            if source_config.pagination_pattern and source_config.max_pages > 1:
                paginated_urls = await self._extract_from_paginated_source(
                    source_name, source_config
                )
                urls.extend(paginated_urls)
            
            logger.info(
                "Source URL extraction completed",
                source=source_name,
                urls_found=len(urls)
            )
            
            return urls
            
        except Exception as e:
            logger.error(
                "Failed to extract URLs from source",
                source=source_name,
                error=str(e)
            )
            raise
    
    async def _extract_from_paginated_source(
        self, 
        source_name: str, 
        source_config: SourceBaseConfig
    ) -> List[str]:
        """
        Extract URLs from paginated source (pages 2 onwards).
        
        Args:
            source_name: Name of the source
            source_config: Configuration for the source
            
        Returns:
            List of URLs from paginated pages
        """
        all_urls = []
        
        for page in range(2, min(source_config.max_pages + 1, 11)):  # Limit to 10 pages max
            try:
                # Construct paginated URL (basic implementation)
                if source_config.pagination_pattern:
                    paginated_url = source_config.pagination_pattern.format(page=page)
                else:
                    # Fallback: append page parameter
                    paginated_url = f"{source_config.listing_url}?page={page}"
                
                logger.info(
                    "Extracting from paginated page",
                    source=source_name,
                    page=page,
                    url=paginated_url
                )
                
                # Apply source-specific delay
                await asyncio.sleep(source_config.request_delay)
                
                page_urls = await self.extract_job_urls(
                    paginated_url,
                    source_name=source_name
                )
                
                if not page_urls:
                    logger.info(
                        "No URLs found on page, stopping pagination",
                        source=source_name,
                        page=page
                    )
                    break
                
                all_urls.extend(page_urls)
                
            except Exception as e:
                logger.error(
                    "Failed to extract from paginated page",
                    source=source_name,
                    page=page,
                    error=str(e)
                )
                # Continue with next page
                continue
        
        logger.info(
            "Pagination extraction completed",
            source=source_name,
            total_paginated_urls=len(all_urls)
        )
        
        return all_urls