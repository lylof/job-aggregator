"""
Enhanced Detail Scraper for Phase 2 - Rich data extraction.
This service implements Stage 2 processing that extracts clean Markdown content
and produces comprehensive JSON-structured data using AI.
"""
import asyncio
import time
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from ..config import SourceRegistry
from ..models_enriched import (
    EnrichedJobData, ExtractionMetadata, PipelineMetadata, 
    ExtractionMethod, calculate_data_quality_score,
    validate_stage2_structured_data
)
from .jina_client import JinaClient
from .gemini_service import GeminiService

logger = structlog.get_logger(__name__)

class EnhancedDetailScraper:
    """
    Enhanced Detail Scraper for Stage 2 processing.
    This service extracts rich, structured job data using:
    1. Optimized Jina Reader parameters per source
    2. Expert Gemini prompts for comprehensive JSON structuration
    3. Quality assessment and validation
    4. Comprehensive error handling and fallback
    """
    
    def __init__(
        self, 
        jina_client: Optional[JinaClient] = None,
        gemini_service: Optional[GeminiService] = None
    ):
        """
        Initialize the Enhanced Detail Scraper.
        Args:
            jina_client: Optional JinaClient instance
            gemini_service: Optional GeminiService instance
        """
        self.jina_client = jina_client or JinaClient()
        self.gemini_service = gemini_service or GeminiService()
        self.source_registry = SourceRegistry()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.jina_client, '__aexit__'):
            await self.jina_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_enriched_job_data(
        self, 
        job_url: str, 
        source_name: str
    ) -> Optional[EnrichedJobData]:
        """
        Extract enriched job data using Stage 2 processing.
        This is the main method that orchestrates:
        1. Source configuration loading
        2. Optimized Markdown extraction
        3. AI-powered JSON structuration
        4. Quality assessment and validation
        
        Args:
            job_url: URL of the job posting
            source_name: Name of the source (for configuration)
            
        Returns:
            EnrichedJobData object or None if extraction fails
        """
        correlation_id = self._generate_correlation_id(job_url)
        logger.info("Starting Stage 2 enriched extraction", 
                   url=job_url, 
                   source=source_name,
                   correlation_id=correlation_id)
        
        start_time = time.time()
        
        try:
            # 1. Load and validate source configuration
            source_config = self.source_registry.get_source(source_name)
            if not source_config:
                logger.error("Source configuration not found", 
                           source=source_name,
                           correlation_id=correlation_id)
                return None
            
            # Check if Stage 2 is enabled for this source
            if not source_config.is_stage2_enabled():
                logger.info("Stage 2 not enabled for source", 
                          source=source_name,
                          correlation_id=correlation_id)
                return None
            
            # 2. Extract optimized Markdown content
            markdown_start = time.time()
            stage2_markdown = await self._extract_optimized_markdown(
                job_url, source_config, correlation_id
            )
            markdown_duration = int((time.time() - markdown_start) * 1000)
            
            if not stage2_markdown:
                logger.warning("Failed to extract markdown content", 
                             url=job_url,
                             correlation_id=correlation_id)
                return None
            
            # 3. Structure data with Gemini expert
            gemini_start = time.time()
            stage2_structured = await self._structure_with_gemini_expert(
                stage2_markdown, job_url, source_config, correlation_id
            )
            gemini_duration = int((time.time() - gemini_start) * 1000)
            
            if not stage2_structured:
                logger.warning("Failed to structure data with Gemini", 
                             url=job_url,
                             correlation_id=correlation_id)
                return None
            
            # 4. Calculate quality score and validate
            quality_score = calculate_data_quality_score(stage2_structured)
            validation_errors = validate_stage2_structured_data(stage2_structured)
            
            # 5. Create enriched job data object
            total_duration = int((time.time() - start_time) * 1000)
            
            enriched_job = EnrichedJobData(
                source_url=job_url,
                stage2_markdown=stage2_markdown,
                stage2_structured=stage2_structured,
                stage2_processing_time_ms=total_duration,
                extraction_quality_score=quality_score,
                validation_errors=validation_errors,
                extraction_metadata=ExtractionMetadata(
                    extraction_timestamp=datetime.utcnow(),
                    processing_duration_ms=total_duration,
                    content_length=len(stage2_markdown),
                    content_quality_score=quality_score,
                    source_site=source_name,
                    jina_model_version="reader-lm-1.5",
                    extraction_method=ExtractionMethod.JINA_ENHANCED
                ),
                pipeline_metadata=PipelineMetadata(
                    reader_duration_ms=markdown_duration,
                    gemini_duration_ms=gemini_duration,
                    total_api_calls=2,  # Jina + Gemini
                    pipeline_version="2.1"
                )
            )
            
            logger.info("Stage 2 extraction completed successfully",
                       url=job_url,
                       quality_score=quality_score,
                       processing_time_ms=total_duration,
                       validation_errors=len(validation_errors),
                       correlation_id=correlation_id)
            
            return enriched_job
            
        except Exception as e:
            logger.error("Stage 2 extraction failed",
                        url=job_url,
                        error=str(e),
                        correlation_id=correlation_id)
            return None
    
    async def extract_multiple_enriched_jobs(
        self,
        job_urls: List[str],
        source_name: str,
        max_concurrent: int = 5
    ) -> List[EnrichedJobData]:
        """
        Extract enriched data for multiple job URLs with concurrency control.
        
        Args:
            job_urls: List of job URLs to process
            source_name: Name of the source
            max_concurrent: Maximum concurrent extractions
            
        Returns:
            List of successfully extracted EnrichedJobData objects
        """
        logger.info("Starting batch Stage 2 extraction",
                   total_urls=len(job_urls),
                   source=source_name,
                   max_concurrent=max_concurrent)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_semaphore(url: str) -> Optional[EnrichedJobData]:
            async with semaphore:
                return await self.extract_enriched_job_data(url, source_name)
        
        # Execute all extractions concurrently
        tasks = [extract_with_semaphore(url) for url in job_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        enriched_jobs = []
        for i, result in enumerate(results):
            if isinstance(result, EnrichedJobData):
                enriched_jobs.append(result)
            elif isinstance(result, Exception):
                logger.error("Batch extraction failed for URL",
                           url=job_urls[i],
                           error=str(result))
        
        success_rate = len(enriched_jobs) / len(job_urls) if job_urls else 0
        logger.info("Batch Stage 2 extraction completed",
                   successful=len(enriched_jobs),
                   total=len(job_urls),
                   success_rate=f"{success_rate:.2%}")
        
        return enriched_jobs
    
    async def _extract_optimized_markdown(
        self,
        job_url: str,
        source_config,
        correlation_id: str
    ) -> Optional[str]:
        """
        Extract optimized Markdown content using Stage 2 Jina parameters.
        
        Args:
            job_url: URL to extract content from
            source_config: Source configuration with Stage 2 parameters
            correlation_id: Correlation ID for logging
            
        Returns:
            Clean Markdown content or None if extraction fails
        """
        try:
            # Get Stage 2 optimized Jina parameters
            jina_params = source_config.get_stage2_jina_params()
            
            logger.debug("Extracting optimized markdown",
                        url=job_url,
                        jina_params=jina_params,
                        correlation_id=correlation_id)
            
            # Extract content with optimized parameters using JinaClient.make_request
            response_data = await self.jina_client.make_request(job_url, jina_params)
            content = response_data.get("content", "") if isinstance(response_data, dict) else ""
            
            if not content or len(content.strip()) < 100:
                logger.warning("Extracted content too short or empty",
                             url=job_url,
                             content_length=len(content) if content else 0,
                             correlation_id=correlation_id)
                return None
            
            # Basic content quality validation
            if not self._validate_content_quality(content):
                logger.warning("Content quality validation failed",
                             url=job_url,
                             correlation_id=correlation_id)
                return None
            
            return content.strip()
            
        except Exception as e:
            logger.error("Markdown extraction failed",
                        url=job_url,
                        error=str(e),
                        correlation_id=correlation_id)
            return None
    
    async def _structure_with_gemini_expert(
        self,
        markdown_content: str,
        job_url: str,
        source_config,
        correlation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Structure markdown content using Gemini expert prompt.
        
        Args:
            markdown_content: Clean markdown content to structure
            job_url: Original job URL for context
            source_config: Source configuration
            correlation_id: Correlation ID for logging
            
        Returns:
            Structured job data dictionary or None if structuration fails
        """
        try:
            # Build expert prompt for comprehensive structuration
            expert_prompt = self._build_expert_prompt(markdown_content, job_url)
            
            # Get Gemini configuration for this source
            gemini_config = source_config.get_stage2_gemini_config()
            
            logger.debug("Structuring content with Gemini expert",
                        content_length=len(markdown_content),
                        gemini_config=gemini_config,
                        correlation_id=correlation_id)
            
            # Call Gemini with expert prompt
            structured_data = await self.gemini_service.structure_job_data_expert(
                expert_prompt,
                **gemini_config
            )
            
            if not structured_data:
                logger.warning("Gemini returned empty structured data",
                             correlation_id=correlation_id)
                return None
            
            # Validate structured data
            if not isinstance(structured_data, dict):
                logger.warning("Gemini returned non-dict structured data",
                             data_type=type(structured_data).__name__,
                             correlation_id=correlation_id)
                return None
            
            return structured_data
            
        except Exception as e:
            logger.error("Gemini structuration failed",
                        error=str(e),
                        correlation_id=correlation_id)
            return None
    
    def _build_expert_prompt(self, markdown_content: str, job_url: str) -> str:
        """
        Build comprehensive expert prompt for Gemini structuration.
        
        Args:
            markdown_content: Clean markdown content
            job_url: Original job URL
            
        Returns:
            Expert prompt string
        """
        return f"""Tu es un expert en extraction de données d'offres d'emploi au Togo. 
Analyse ce contenu d'offre d'emploi et structure-le en JSON complet et précis.

URL source: {job_url}

Contenu à analyser:
{markdown_content}

Produis un JSON structuré avec TOUS les champs suivants (utilise null si l'information n'est pas disponible):

{{
  "title": "Titre exact du poste",
  "company": "Nom de l'entreprise",
  "location": {{
    "city": "Ville (ex: Lomé)",
    "region": "Région (ex: Maritime)",
    "country": "Togo"
  }},
  "contract": {{
    "type": "CDI/CDD/Stage/Freelance/Intérim",
    "duration": "Durée si CDD/Stage",
    "start_date": "Date de début si mentionnée (format YYYY-MM-DD)"
  }},
  "salary": {{
    "min": montant_minimum_numerique,
    "max": montant_maximum_numerique,
    "currency": "XOF/EUR/USD",
    "period": "monthly/yearly/daily",
    "negotiable": true/false
  }},
  "requirements": {{
    "experience": "Expérience requise (ex: 2-3 ans)",
    "education": "Niveau d'études (ex: Bac+3)",
    "skills": ["Compétence 1", "Compétence 2"],
    "languages": ["Français", "Anglais"]
  }},
  "description": {{
    "summary": "Résumé du poste",
    "missions": ["Mission 1", "Mission 2"],
    "profile": "Profil recherché",
    "benefits": ["Avantage 1", "Avantage 2"]
  }},
  "application": {{
    "deadline": "Date limite (format YYYY-MM-DD)",
    "email": "Email de candidature",
    "phone": "Téléphone",
    "instructions": "Instructions de candidature"
  }},
  "metadata": {{
    "publication_date": "Date de publication (format YYYY-MM-DD)",
    "sector": "Secteur d'activité",
    "department": "Département/Service"
  }}
}}

INSTRUCTIONS CRITIQUES:
- Extrais TOUTES les informations disponibles
- Utilise null pour les champs manquants, ne les omets pas
- Convertis les montants en nombres (sans espaces ni symboles)
- Normalise les dates au format YYYY-MM-DD
- Sois précis et fidèle au contenu original
- Pour les listes, inclus tous les éléments mentionnés

Réponds UNIQUEMENT avec le JSON, sans texte additionnel."""
    
    def _validate_content_quality(self, content: str) -> bool:
        """
        Validate basic content quality for Stage 2 processing.
        
        Args:
            content: Extracted content to validate
            
        Returns:
            True if content meets quality standards
        """
        if not content or len(content.strip()) < 100:
            return False
        
        # Check for minimum job-related keywords
        job_keywords = ['emploi', 'poste', 'candidat', 'expérience', 'compétence', 'mission']
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in content_lower)
        
        return keyword_count >= 2
    
    def _generate_correlation_id(self, job_url: str) -> str:
        """
        Generate correlation ID for tracking.
        
        Args:
            job_url: Job URL to generate ID from
            
        Returns:
            Correlation ID string
        """
        return hashlib.md5(f"{job_url}_{int(time.time())}".encode()).hexdigest()[:8]