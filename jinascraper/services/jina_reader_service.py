"""Jina Reader service for web content extraction."""

import asyncio
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import config
from ..models import JobOffer, ExtractionMethod, ExtractionMetadata
from ..sources_config import SourceConfig, TogoJobSources


logger = structlog.get_logger(__name__)


class JinaReaderError(Exception):
    """Base exception for Jina Reader service errors."""
    pass


class JinaAPIError(JinaReaderError):
    """Exception for Jina API-related errors."""
    pass


class JinaReaderService:
    """Service for extracting web content using Jina AI Reader API."""
    
    def __init__(self):
        self.api_key = config.jina_api_key
        self.base_url = config.jina_base_url
        self.timeout = config.timeout_seconds
        self.max_concurrent = config.max_concurrent_requests
        self.delay = config.request_delay_seconds
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "JinaJobScraper/1.0.0",
                "Accept": "application/json",
            },
            limits=httpx.Limits(max_connections=self.max_concurrent)
        )
        
        # Rate limiting semaphore
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a rate-limited request to Jina Reader API."""
        async with self._semaphore:
            start_time = time.time()
            
            try:
                # Add delay between requests
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
                
                # For Jina Reader API, we construct the URL differently
                # Format: https://r.jina.ai/{target_url}
                jina_url = f"{self.base_url.rstrip('/')}/{url}"
                
                # Prepare headers for the request
                headers = {}
                
                # Handle CSS selector as header instead of parameter
                if params and "css_selector_only" in params:
                    headers["X-Target-Selector"] = params["css_selector_only"]
                    # Remove from params since it's now a header
                    params = {k: v for k, v in params.items() if k != "css_selector_only"}
                
                logger.info("Making Jina Reader request", url=jina_url, params=params, headers=headers)
                
                response = await self.client.get(jina_url, params=params or {}, headers=headers)
                response.raise_for_status()
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # Jina Reader API returns JSON with content in data.content
                response_json = response.json()
                
                if "data" in response_json and "content" in response_json["data"]:
                    content = response_json["data"]["content"]
                    title = response_json["data"].get("title", "")
                    description = response_json["data"].get("description", "")
                else:
                    # Fallback to plain text if JSON structure is different
                    content = response.text
                    title = ""
                    description = ""
                
                data = {
                    "content": content,
                    "title": title,
                    "description": description,
                    "url": url,
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time,
                    "raw_response": response_json if "data" in response_json else None
                }
                
                logger.info(
                    "Jina Reader request successful",
                    url=jina_url,
                    status_code=response.status_code,
                    processing_time_ms=processing_time,
                    content_length=len(content)
                )
                
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Jina Reader HTTP error",
                    url=jina_url,
                    status_code=e.response.status_code,
                    error=str(e)
                )
                raise JinaAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            
            except httpx.RequestError as e:
                logger.error("Jina Reader request error", url=jina_url, error=str(e))
                raise JinaAPIError(f"Request failed: {str(e)}")
    
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
                source_config = TogoJobSources.get_source(source_name)
            
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
            response_data = await self._make_request(listing_url, params)
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
            raise JinaReaderError(f"URL extraction failed: {str(e)}")
    
    async def extract_job_data(
        self, 
        job_url: str, 
        source_site: str,
        source_name: Optional[str] = None,
        use_reader_lm: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured job data from a job posting URL using Jina Reader.
        Optimized for Stage 2 (Analysis) with ReaderLM-v2 for maximum quality.
        
        Args:
            job_url: URL of the job posting
            source_site: Name of the source job site
            source_name: Name of the source (for site-specific configuration)
            use_reader_lm: Whether to use ReaderLM-v2 for enhanced extraction
            
        Returns:
            Dictionary containing extracted job data, or None if extraction failed
        """
        try:
            logger.info("Extracting job data", url=job_url, source_site=source_site, source=source_name)
            
            start_time = time.time()
            
            # Get source-specific configuration
            source_config = None
            if source_name:
                source_config = TogoJobSources.get_source(source_name)
            
            # Stage 2 optimized parameters for Jina Reader
            params = {
                "timeout": "60",
                "with_generated_alt": "true"
            }
            
            # Use ReaderLM-v2 based on source config or parameter
            reader_lm_enabled = use_reader_lm
            if source_config:
                reader_lm_enabled = source_config.use_reader_lm
            
            if reader_lm_enabled:
                params["use_reader_lm_v2"] = "true"
                logger.info("Using ReaderLM-v2 for enhanced extraction")
            
            # Use source-specific exclusion selectors
            exclude_selectors = "header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
            if source_config and source_config.css_selector_exclude:
                exclude_selectors = source_config.css_selector_exclude
            
            params["css_selector_excluding"] = exclude_selectors
            
            # Use Jina Reader with Stage 2 configuration
            response_data = await self._make_request(job_url, params)
            content = response_data.get("content", "")
            
            if not content:
                logger.warning("No content extracted from job page", url=job_url)
                return None
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Create extraction metadata
            metadata = ExtractionMetadata(
                method=ExtractionMethod.JINA,
                source_site=source_site,
                processing_time_ms=processing_time
            )
            
            # Parse job content to structured data
            job_data = self._parse_job_content(content, job_url, metadata)
            
            logger.info(
                "Job data extracted successfully",
                url=job_url,
                source_site=source_site,
                processing_time_ms=processing_time,
                has_title=bool(job_data.get("title")),
                has_company=bool(job_data.get("company")),
                content_length=len(content),
                used_reader_lm=use_reader_lm
            )
            
            return job_data
            
        except Exception as e:
            logger.error(
                "Failed to extract job data",
                url=job_url,
                source_site=source_site,
                error=str(e)
            )
            return None
    
    async def extract_multiple_jobs(
        self, 
        job_urls: List[str], 
        source_site: str
    ) -> List[Dict[str, Any]]:
        """
        Extract job data from multiple URLs concurrently.
        
        Args:
            job_urls: List of job posting URLs
            source_site: Name of the source job site
            
        Returns:
            List of extracted job data dictionaries
        """
        logger.info(
            "Starting batch job extraction",
            source_site=source_site,
            total_urls=len(job_urls)
        )
        
        # Create extraction tasks
        tasks = [
            self.extract_job_data(url, source_site)
            for url in job_urls
        ]
        
        # Execute tasks concurrently with rate limiting
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful extractions
        successful_jobs = []
        errors = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Job extraction failed",
                    url=job_urls[i],
                    error=str(result)
                )
                errors += 1
            elif result is not None:
                successful_jobs.append(result)
        
        logger.info(
            "Batch job extraction completed",
            source_site=source_site,
            total_urls=len(job_urls),
            successful=len(successful_jobs),
            errors=errors
        )
        
        return successful_jobs
    
    def _extract_job_urls_from_jina_content(
        self, 
        content: str, 
        base_url: str, 
        source_config: Optional[SourceConfig] = None
    ) -> List[str]:
        """
        Extract job URLs from Jina Reader content with "Buttons & Links" section.
        
        Jina Reader with gather_all_links_at_the_end=true creates a section
        at the end with all links found on the page.
        """
        import re
        
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
        
        # Extract URLs that look like job postings
        job_url_patterns = [
            r'https?://[^\s<>"\']+(?:job|emploi|offre|poste|career|vacancy)[^\s<>"\']*',
            r'https?://[^\s<>"\']+/(?:jobs?|emplois?|offres?|postes?|careers?|vacancies?)[^\s<>"\']*',
            r'https?://[^\s<>"\']+[?&](?:job|emploi|offre)(?:_?id|Id)?=\d+[^\s<>"\']*'
        ]
        
        all_urls = []
        for pattern in job_url_patterns:
            urls = re.findall(pattern, links_content, re.IGNORECASE)
            all_urls.extend(urls)
        
        # Clean and validate URLs
        valid_urls = []
        base_domain = urlparse(base_url).netloc
        
        for url in all_urls:
            try:
                # Clean URL (remove trailing punctuation)
                url = re.sub(r'[.,;:!?)\]]+$', '', url)
                
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
    
    async def extract_urls_from_all_sources(self) -> Dict[str, List[str]]:
        """
        Extract job URLs from all configured Togo sources in parallel.
        
        Returns:
            Dictionary mapping source names to lists of job URLs
        """
        logger.info("Starting parallel URL extraction from all Togo sources")
        
        sources = TogoJobSources.get_all_sources()
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
        source_config: SourceConfig
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
        source_config: SourceConfig
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
                    import re
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
    
    def _parse_job_content(
        self, 
        content: str, 
        source_url: str, 
        metadata: ExtractionMetadata
    ) -> Dict[str, Any]:
        """
        Parse job content to extract structured data using regex patterns.
        
        This extracts basic information before sending to Gemini for enhancement.
        """
        import re
        
        # Enhanced extraction logic with regex patterns
        job_data = {
            "title": self._extract_title_enhanced(content),
            "company": self._extract_company_enhanced(content),
            "location": self._extract_location(content),
            "contract_type": self._extract_contract_type(content),
            "experience_level": self._extract_experience_level(content),
            "education_level": self._extract_education_level(content),
            "sector": self._extract_sector(content),
            "description": self._extract_description(content),
            "missions": self._extract_missions(content),
            "profile": self._extract_profile(content),
            "source_url": source_url,
            "extraction_method": ExtractionMethod.JINA,
            "extraction_metadata": metadata.dict(),
            "raw_data": {"content": content}
        }
        
        return job_data
    
    def _extract_title_enhanced(self, content: str) -> Optional[str]:
        """Extract job title with enhanced patterns."""
        import re
        
        # Pattern 1: Title in header (most common)
        title_patterns = [
            r'Offre d\'emploi Togo\s*:\s*(.+?)\s*-\s*Lomé',
            r'###\s*(.+?)\s*\n',
            r'Poste proposé\s*:\s*(.+?)(?:\n|$)',
            r'^(.+?)\s*=+\s*$',  # Title followed by equals signs
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up common artifacts
                title = re.sub(r'\s*H/F\s*$', ' H/F', title)
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 5 and len(title) < 100:
                    return title
        
        return None
    
    def _extract_company_enhanced(self, content: str) -> Optional[str]:
        """Extract company name with enhanced patterns."""
        import re
        
        company_patterns = [
            r'###\s*\[([^\]]+)\]',  # [COMPANY NAME] in markdown links
            r'\*\*\[([^\]]+)\]\(',  # **[COMPANY NAME]( in bold links
            r'Entreprise[^:]*:\s*([^\n]+)',
            r'Recruteur[^:]*:\s*([^\n]+)',
            r'Société[^:]*:\s*([^\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common artifacts
                company = re.sub(r'^\*\*|\*\*$', '', company)  # Remove bold markers
                company = re.sub(r'^\[|\]$', '', company)  # Remove brackets
                if len(company) > 2 and len(company) < 100:
                    return company
        
        return None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract job location."""
        import re
        
        location_patterns = [
            r'Région de\s*:\s*([^\n]+)',
            r'Ville\s*:\s*([^\n]+)',
            r'Lieu\s*:\s*([^\n]+)',
            r'Localisation\s*:\s*([^\n]+)',
            r'\b(Lomé|Kara|Sokodé|Kpalimé|Atakpamé|Dapaong|Tsévié)\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if location and len(location) < 50:
                    return location
        
        return None
    
    def _extract_contract_type(self, content: str) -> Optional[str]:
        """Extract contract type."""
        import re
        
        contract_patterns = [
            r'Type de contrat\s*:\s*([^\n]+)',
            r'Contrat proposé\s*:\s*([^\n]+)',
            r'\b(CDI|CDD|Stage|Freelance|Intérim|Temps partiel|Temps plein)\b'
        ]
        
        for pattern in contract_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                contract = match.group(1).strip()
                if contract and len(contract) < 50:
                    return contract
        
        return None
    
    def _extract_experience_level(self, content: str) -> Optional[str]:
        """Extract required experience level."""
        import re
        
        experience_patterns = [
            r'Niveau d\'expérience\s*:\s*([^\n]+)',
            r'Expérience\s*:\s*([^\n]+)',
            r'Expérience entre (\d+) ans et (\d+) ans',
            r'(\d+)\s*ans?\s*d\'expérience'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                experience = match.group(1).strip() if match.lastindex == 1 else match.group(0)
                if experience and len(experience) < 100:
                    return experience
        
        return None
    
    def _extract_education_level(self, content: str) -> Optional[str]:
        """Extract required education level."""
        import re
        
        education_patterns = [
            r'Niveau d\'études\s*:\s*([^\n]+)',
            r'Formation\s*:\s*([^\n]+)',
            r'\b(Bac\+\d+|Bac|Master|Licence|Doctorat)\b'
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                education = match.group(1).strip() if match.lastindex == 1 else match.group(0)
                if education and len(education) < 50:
                    return education
        
        return None
    
    def _extract_sector(self, content: str) -> Optional[str]:
        """Extract business sector."""
        import re
        
        sector_patterns = [
            r'Secteur d\'activité\s*:\s*([^\n]+)',
            r'Domaine\s*:\s*([^\n]+)',
            r'Secteur\s*:\s*([^\n]+)'
        ]
        
        for pattern in sector_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sector = match.group(1).strip()
                if sector and len(sector) < 100:
                    return sector
        
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract job description."""
        import re
        
        # Look for description sections
        desc_patterns = [
            r'Description[^:]*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Détails de l\'annonce[^:]*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Nous sommes à la recherche[^.]*\.([^#]+?)(?=\n#|\n\*\*|$)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                if description and len(description) > 50:
                    return description[:1000]  # Limit to 1000 chars
        
        return None
    
    def _extract_missions(self, content: str) -> Optional[str]:
        """Extract job missions/responsibilities."""
        import re
        
        missions_patterns = [
            r'Missions?\s*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Responsabilités?\s*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Tâches?\s*:\s*([^#]+?)(?=\n#|\n\*\*|$)'
        ]
        
        for pattern in missions_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                missions = match.group(1).strip()
                if missions and len(missions) > 20:
                    return missions[:800]  # Limit to 800 chars
        
        return None
    
    def _extract_profile(self, content: str) -> Optional[str]:
        """Extract required profile/qualifications."""
        import re
        
        profile_patterns = [
            r'Profil recherché[^:]*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Qualifications?\s*:\s*([^#]+?)(?=\n#|\n\*\*|$)',
            r'Compétences?\s*:\s*([^#]+?)(?=\n#|\n\*\*|$)'
        ]
        
        for pattern in profile_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                profile = match.group(1).strip()
                if profile and len(profile) > 20:
                    return profile[:800]  # Limit to 800 chars
        
        return None
    
    def _extract_title(self, lines: List[str]) -> Optional[str]:
        """Extract job title from content lines."""
        # Look for lines that might be titles (first few non-empty lines)
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                return line
        return None
    
    def _extract_company(self, lines: List[str]) -> Optional[str]:
        """Extract company name from content lines."""
        # Basic company extraction logic
        for line in lines[:20]:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['company', 'entreprise', 'société']):
                # Extract company name from this line
                parts = line.split()
                if len(parts) > 1:
                    return ' '.join(parts[1:3])  # Take next 1-2 words
        return None