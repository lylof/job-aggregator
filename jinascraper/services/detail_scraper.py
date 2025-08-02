"""Detail Scraper for extracting structured job data from job pages (Stage 2)."""

import asyncio
import time
import re
from typing import List, Dict, Any, Optional
import structlog

from ..config import SourceRegistry, JINA_BASE_CONFIG, SourceBaseConfig
from ..models import JobOffer, ExtractionMethod, ExtractionMetadata
from .jina_client import JinaClient
from .gemini_service import GeminiService
from .openrouter_service import OpenRouterService
import os


logger = structlog.get_logger(__name__)


class DetailScraper:
    """Service for extracting structured job data from job pages (Stage 2)."""
    
    def __init__(self, jina_client: Optional[JinaClient] = None, allow_raw: Optional[bool] = None):
        """
        Initialize the DetailScraper.
        
        Args:
            jina_client: Optional JinaClient instance. If not provided, a new one will be created.
            allow_raw: Accept raw markdown when structuring fails (overrides ALLOW_RAW_ONLY env)
        """
        self.jina_client = jina_client or JinaClient()
        self.gemini = GeminiService()
        self.fallback = OpenRouterService()
        # Allow-raw flag via arg or env
        if allow_raw is None:
            env_val = os.getenv("ALLOW_RAW_ONLY", "0").lower()
            self.allow_raw = env_val in ("1", "true", "yes", "on")
        else:
            self.allow_raw = allow_raw
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not isinstance(self.jina_client, JinaClient):
            self.jina_client = await self.jina_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.jina_client:
            await self.jina_client.__aexit__(exc_type, exc_val, exc_tb)
    
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
                source_config = SourceRegistry.get_source(source_name)
            
            # Get Stage 2 configuration parameters
            if source_config:
                try:
                    # Try to get Stage 2 configuration from source
                    params = source_config.get_stage2_jina_params()
                    logger.info("Using Stage 2 Jina configuration from source", 
                               source=source_name, params=params)
                except (AttributeError, Exception) as e:
                    # Fallback to default Stage 2 parameters
                    params = {
                        "timeout": "60",
                        "with_generated_alt": "true",
                        "css_selector_excluding": "header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
                    }
                    logger.info("Using default Stage 2 parameters (config method failed)", error=str(e))
            else:
                # Fallback to default Stage 2 parameters
                params = {
                    "timeout": "60",
                    "with_generated_alt": "true",
                    "css_selector_excluding": "header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
                }
                logger.info("Using default Stage 2 parameters (no source config)")
            
            # ReaderLM-v2 supprimé - utilisation du moteur standard uniquement
            
            # Use Jina Reader with Stage 2 configuration
            response_data = await self.jina_client.make_request(job_url, params)
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
            
            # First-pass regex parsing (baseline)
            job_data = self._parse_job_content(content, job_url, metadata)

            # Try Gemini structuring to improve quality (threshold lowered in GeminiService)
            structured = None
            try:
                structured = await self.gemini.structure_job_data(content, job_url, source_site)
            except Exception as e:
                logger.warning("Gemini structuring raised exception, will try fallback", url=job_url, error=str(e))

            # Fallback LLM if Gemini failed
            if not structured:
                try:
                    structured = await self.fallback.structure_job_data(content, job_url)
                except Exception as e:
                    logger.error("LLM fallback failed with exception", url=job_url, error=str(e))
                    structured = None

            # Merge structured fields when available
            if structured and isinstance(structured, dict):
                merged = {**job_data}
                # Prefer structured fields if present
                for k in ("title", "company", "location", "contract_type", "salary_range",
                          "experience_level", "education_level", "sector", "description"):
                    if k in structured and structured[k]:
                        merged[k] = structured[k]
                # Attach raw structured payload and quality info if provided
                merged["structured_json"] = structured
                merged["extraction_method"] = structured.get("extraction_method", ExtractionMethod.GEMINI)
                job_data = merged

            # If still no structured and allow_raw enabled, keep raw record
            if not structured and self.allow_raw:
                job_data.setdefault("quality_metrics", {
                    "completeness_score": 0.0,
                    "quality_issues": ["structured_json_missing_allow_raw"],
                    "field_coverage": {}
                })
                job_data["extraction_method"] = "raw_only"

            logger.info(
                "Job data extracted successfully",
                url=job_url,
                source_site=source_site,
                processing_time_ms=processing_time,
                has_title=bool(job_data.get("title")),
                has_company=bool(job_data.get("company")),
                content_length=len(content),
                used_reader_lm=use_reader_lm,
                has_structured=bool(job_data.get("structured_json"))
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
                location = match.group(1).strip() if match.lastindex == 1 else match.group(0)
                if location and len(location) < 50:
                    return location
        
        return None
    
    def _extract_contract_type(self, content: str) -> Optional[str]:
        """Extract contract type."""
        contract_patterns = [
            r'Type de contrat\s*:\s*([^\n]+)',
            r'Contrat proposé\s*:\s*([^\n]+)',
            r'\b(CDI|CDD|Stage|Freelance|Intérim|Temps partiel|Temps plein)\b'
        ]
        
        for pattern in contract_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                contract = match.group(1).strip() if match.lastindex == 1 else match.group(0)
                if contract and len(contract) < 50:
                    return contract
        
        return None
    
    def _extract_experience_level(self, content: str) -> Optional[str]:
        """Extract required experience level."""
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