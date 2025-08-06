"""Google Gemini service for structured job data extraction."""

import asyncio
import json
import time
from jinascraper.utils.type_helpers import Dict, Any, Optional, List
import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from jinascraper.config import config
from jinascraper.models import JobOffer, ExtractionMethod, ExtractionMetadata


logger = structlog.get_logger(__name__)


class GeminiError(Exception):
    """Base exception for Gemini service errors."""
    pass


class GeminiAPIError(GeminiError):
    """Exception for Gemini API-related errors."""
    pass


class GeminiValidationError(GeminiError):
    """Exception for Gemini response validation errors."""
    pass


class GeminiService:
    """Service for structuring job data using Google Gemini AI with multi-key rotation and backoff."""
    
    def __init__(self):
        # Gestion multi-clés
        self.api_keys = getattr(config, "gemini_api_keys", [])
        self.model_name = config.gemini_model
        if not self.api_keys:
            # fallback compat
            single = getattr(config, "gemini_api_key", "")
            self.api_keys = [single] if single else []
        if not self.api_keys:
            raise ValueError("No Gemini API key configured. Set GEMINI_API_KEYS or GEMINI_API_KEY.")
        
        # État de rotation et circuit-breaker léger par clé
        self._key_index = 0
        self._key_failures = {k: 0 for k in self.api_keys}
        self._key_cooldown_until = {k: 0.0 for k in self.api_keys}
        self._cooldown_base_seconds = 30.0  # base cooldown après 429/5xx
        self._max_cooldown_seconds = 600.0  # 10 minutes
        
        # Configure Gemini avec la première clé active
        self._configure_gemini(self._current_key())
        
        # Modèle avec configuration de sortie structurée
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        # Rate limiting local (anti-burst)
        self.rate_limit_delay = 1.0
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()
        
        logger.info("GeminiService initialized", model=self.model_name, keys_configured=len(self.api_keys))
    
    async def _enforce_rate_limit(self):
        """Enforce client-side rate limiting."""
        async with self._request_lock:
            now = time.time()
            dt = now - self._last_request_time
            if dt < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - dt
                logger.debug("Gemini rate limiting: sleeping", sleep_seconds=sleep_time)
                await asyncio.sleep(sleep_time)
            self._last_request_time = time.time()
    
    def _get_job_extraction_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for job data extraction."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Job title or position name"
                },
                "company": {
                    "type": "string", 
                    "description": "Company or organization name"
                },
                "location": {
                    "type": "string",
                    "description": "Job location (city, region, country)"
                },
                "contract_type": {
                    "type": "string",
                    "description": "Type of contract (CDI, CDD, Stage, Freelance, etc.)"
                },
                "salary_range": {
                    "type": "string",
                    "description": "Salary range or compensation information"
                },
                "experience_level": {
                    "type": "string",
                    "description": "Required experience level (Junior, Senior, etc.)"
                },
                "education_level": {
                    "type": "string",
                    "description": "Required education level (Bac+3, Master, etc.)"
                },
                "sector": {
                    "type": "string",
                    "description": "Industry sector or domain"
                },
                "description": {
                    "type": "string",
                    "description": "Job description summary"
                },
                "missions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of main missions and responsibilities"
                },
                "required_skills": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of required skills and competencies"
                },
                "profile_description": {
                    "type": "string",
                    "description": "Ideal candidate profile description"
                },
                "application_deadline": {
                    "type": "string",
                    "description": "Application deadline if mentioned"
                },
                "posted_date": {
                    "type": "string",
                    "description": "Job posting date if mentioned"
                }
            },
            "required": ["title", "company"],
            "additionalProperties": False
        }
    
    def _create_extraction_prompt(self, content: str, source_url: str, source_site: str = None) -> str:
        """Create an optimized prompt for job data extraction based on source type."""
        schema = self._get_job_extraction_schema()
        
        # Detect source type for specialized prompts
        source_specific_instructions = self._get_source_specific_instructions(source_site, source_url)
        
        prompt = f"""Tu es un expert en extraction de données d'offres d'emploi au Togo. Analyse le contenu suivant et extrais les informations structurées selon le schéma JSON fourni.

CONTEXTE:
- Source: {source_site or 'Site d\'emploi togolais'}
- URL: {source_url}
- Pays: Togo (Afrique de l'Ouest)
- Monnaie: Franc CFA (XOF)

RÈGLES D'EXTRACTION:
1. ✅ Extrais UNIQUEMENT les informations explicitement présentes
2. ❌ Ne jamais inventer ou halluciner d'informations
3. 🔍 Si une information n'est pas claire, utilise null
4. 📋 Respecte exactement le schéma JSON fourni
5. 📝 Pour les listes, extrais chaque élément distinct
6. 🔧 Normalise les formats (dates, salaires, lieux)

INSTRUCTIONS SPÉCIFIQUES:
{source_specific_instructions}

NORMALISATION:
- Lieux: "Lomé", "Kara", "Sokodé", etc. (pas "Lomé, Togo")
- Salaires: Inclure "XOF" si montant mentionné
- Dates: Format ISO si possible
- Contrats: "CDI", "CDD", "Stage", "Freelance"
- Expérience: "Junior", "Senior", "X ans", etc.

SCHÉMA JSON REQUIS:
{json.dumps(schema, indent=2, ensure_ascii=False)}

CONTENU À ANALYSER:
{content}

RÉPONSE (JSON valide uniquement):"""
        return prompt
    
    def _get_source_specific_instructions(self, source_site: str, source_url: str) -> str:
        """Get specialized extraction instructions based on source site."""
        if not source_site:
            return "- Extraction générale d'offre d'emploi"
        
        source_lower = source_site.lower()
        
        if "emploi.tg" in source_lower:
            return """- Site: Emploi.tg (principal site d'emploi togolais)
- Structure typique: Titre → Entreprise → Missions → Profil → Conditions
- Attention aux liens markdown [Entreprise](url)
- Salaires souvent "À négocier" ou en XOF
- Lieux principalement Lomé"""
        
        elif "anpe" in source_lower:
            return """- Site: ANPE Togo (service public de l'emploi)
- Structure officielle gouvernementale
- Offres souvent détaillées avec critères précis
- Attention aux références de poste
- Procédures de candidature formelles"""
        
        elif "yop.l-frii" in source_lower:
            return """- Site: YOP L-FRII (ONG et humanitaire)
- Focus sur secteur humanitaire et développement
- Missions souvent internationales
- Critères d'expérience spécifiques
- Attention aux deadlines de candidature"""
        
        elif "linkedin" in source_lower:
            return """- Site: LinkedIn Togo
- Format international standardisé
- Entreprises souvent multinationales
- Compétences techniques détaillées
- Salaires parfois en devises étrangères"""
        
        elif "emploitogo.info" in source_lower:
            return """- Site: EmploiTogo.info
- Actualités et offres d'emploi
- Structure article/news
- Informations parfois dans le texte libre
- Attention aux dates de publication"""
        
        else:
            return f"- Site: {source_site}\n- Extraction adaptée au contexte togolais"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((GeminiAPIError, Exception)),
        reraise=True
    )
    async def _make_gemini_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to Gemini API with retry logic and multi-key rotation."""
        await self._enforce_rate_limit()
        start_time = time.time()
        
        # Essayer autant de clés que possible dans un tour
        tried_keys = set()
        last_error: Optional[Exception] = None
        
        for _ in range(len(self.api_keys)):
            key = self._select_viable_key()
            if not key or key in tried_keys:
                break
            tried_keys.add(key)
            try:
                logger.info("Making Gemini request", prompt_length=len(prompt), key_index=self._key_index)
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.model.generate_content, prompt),
                    timeout=60.0
                )
                processing_time = int((time.time() - start_time) * 1000)
                
                if not response.text:
                    raise GeminiAPIError("Empty response from Gemini")
                
                try:
                    structured_data = json.loads(response.text)
                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse Gemini JSON response, attempting cleanup",
                                   response_text=response.text[:200], error=str(e))
                    cleaned_response = self._clean_json_response(response.text)
                    try:
                        structured_data = json.loads(cleaned_response)
                        logger.info("Successfully parsed cleaned JSON response")
                    except json.JSONDecodeError:
                        logger.error("Failed to parse even cleaned JSON response",
                                     cleaned_response=cleaned_response[:200])
                        raise GeminiValidationError(f"Invalid JSON response: {str(e)}")
                
                # Succès: reset des compteurs sur la clé courante
                self._key_failures[key] = 0
                self._key_cooldown_until[key] = 0.0
                
                logger.info(
                    "Gemini request successful",
                    processing_time_ms=processing_time,
                    response_length=len(response.text),
                    has_title=bool(structured_data.get("title")),
                    has_company=bool(structured_data.get("company"))
                )
                return structured_data
            
            except Exception as e:
                last_error = e
                err_text = str(e).lower()
                is_rate = ("quota" in err_text) or ("rate" in err_text) or ("429" in err_text)
                is_server = ("5" in err_text) or ("unavailable" in err_text)
                
                logger.warning("Gemini request failed on key, will rotate if possible",
                               error=str(e), key_tail=key[-6:] if key else None)
                
                # Marquer la clé en échec et appliquer un cooldown exponentiel
                self._mark_key_failure(key, is_rate or is_server)
                
                # Rotation vers la clé suivante viable
                self._rotate_key()
                # Reconfigurer le client avec la nouvelle clé (si disponible)
                self._configure_gemini(self._current_key())
                # Le retry decorator gère les relances globales; ici on boucle sur les clés
                
        # Si aucune clé n'a réussi, relancer l'erreur
        if last_error:
            if isinstance(last_error, GeminiError):
                raise last_error
            raise GeminiError(f"All Gemini keys failed: {str(last_error)}")
        raise GeminiError("No Gemini key available to make request")
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean and fix common JSON formatting issues in Gemini responses."""
        import re
        
        # Remove markdown code blocks if present
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Remove any text before the first {
        first_brace = cleaned.find('{')
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        # Remove any text after the last }
        last_brace = cleaned.rfind('}')
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        # Fix common JSON issues
        cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas
        cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas in arrays
        
        return cleaned.strip()
    
    def _current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self._key_index % len(self.api_keys)]
    
    def _rotate_key(self):
        if not self.api_keys:
            return
        self._key_index = (self._key_index + 1) % len(self.api_keys)
    
    def _select_viable_key(self) -> Optional[str]:
        """Sélectionne une clé non en cooldown, sinon None."""
        now = time.time()
        for i in range(len(self.api_keys)):
            idx = (self._key_index + i) % len(self.api_keys)
            key = self.api_keys[idx]
            if now >= self._key_cooldown_until.get(key, 0.0):
                # Positionner l'index sur cette clé
                self._key_index = idx
                # Reconfigurer avec cette clé
                self._configure_gemini(key)
                return key
        return None
    
    def _mark_key_failure(self, key: Optional[str], backoffable: bool):
        if not key:
            return
        self._key_failures[key] = self._key_failures.get(key, 0) + 1
        if backoffable:
            # Exponential backoff avec cap
            cooldown = min(self._cooldown_base_seconds * (2 ** (self._key_failures[key] - 1)), self._max_cooldown_seconds)
            self._key_cooldown_until[key] = time.time() + cooldown
            logger.info("Applying cooldown to Gemini key", cooldown_seconds=cooldown, failures=self._key_failures[key])
    
    def _configure_gemini(self, key: Optional[str]):
        if not key:
            return
        try:
            genai.configure(api_key=key)
        except Exception as e:
            logger.warning("Gemini configure failed for key", error=str(e))
    
    def _validate_extraction_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and score the quality of extracted data."""
        quality_metrics = {
            "completeness_score": 0.0,
            "quality_issues": [],
            "field_coverage": {}
        }
        
        # Required fields check
        required_fields = ["title", "company"]
        for field in required_fields:
            if data.get(field):
                quality_metrics["completeness_score"] += 0.3
                quality_metrics["field_coverage"][field] = True
            else:
                quality_metrics["quality_issues"].append(f"Missing required field: {field}")
                quality_metrics["field_coverage"][field] = False
        
        # Important optional fields
        important_fields = ["location", "description", "missions", "required_skills"]
        for field in important_fields:
            if data.get(field):
                quality_metrics["completeness_score"] += 0.1
                quality_metrics["field_coverage"][field] = True
            else:
                quality_metrics["field_coverage"][field] = False
        
        # Data quality checks
        if data.get("title") and len(data["title"]) < 5:
            quality_metrics["quality_issues"].append("Title too short")
        
        if data.get("company") and len(data["company"]) < 2:
            quality_metrics["quality_issues"].append("Company name too short")
        
        if data.get("missions") and isinstance(data["missions"], list):
            if len(data["missions"]) == 0:
                quality_metrics["quality_issues"].append("Empty missions list")
            elif len(data["missions"]) > 10:
                quality_metrics["quality_issues"].append("Too many missions (possible parsing error)")
        
        # Cap the score at 1.0
        quality_metrics["completeness_score"] = min(quality_metrics["completeness_score"], 1.0)
        
        return quality_metrics

    async def structure_job_data(
        self, 
        raw_content: str, 
        source_url: str,
        source_site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Structure raw job content into standardized format using Gemini.
        
        Args:
            raw_content: Raw job content from Jina Reader
            source_url: URL of the job posting
            source_site: Name of the source site
            
        Returns:
            Structured job data dictionary or None if extraction failed
        """
        try:
            logger.info("Structuring job data with Gemini", 
                       url=source_url, content_length=len(raw_content))
            
            start_time = time.time()
            
            # Create optimized extraction prompt
            prompt = self._create_extraction_prompt(raw_content, source_url, source_site)
            
            # Get structured data from Gemini
            structured_data = await self._make_gemini_request(prompt)
            
            # Validate extraction quality
            quality_metrics = self._validate_extraction_quality(structured_data)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Check extraction quality
            # TEMP: Lowered threshold from 0.6 to 0.4 to reduce false negatives and unblock pipeline
            if quality_metrics["completeness_score"] < 0.4:  # Minimum 40% completeness (temporarily relaxed)
                logger.warning("Low quality extraction",
                             completeness_score=quality_metrics["completeness_score"],
                             issues=quality_metrics["quality_issues"])
                return None
            
            # Add metadata
            metadata = ExtractionMetadata(
                method=ExtractionMethod.GEMINI,
                source_site=source_site,
                processing_time_ms=processing_time
            )
            
            # Enrich with metadata and quality info
            enriched_data = {
                **structured_data,
                "source_url": source_url,
                "extraction_method": ExtractionMethod.GEMINI,
                "extraction_metadata": metadata.dict(),
                "quality_metrics": quality_metrics,
                "raw_data": {"content": raw_content}
            }
            
            logger.info(
                "Job data structured successfully",
                url=source_url,
                processing_time_ms=processing_time,
                title=structured_data.get("title", "")[:50],
                company=structured_data.get("company", "")[:30],
                completeness_score=quality_metrics["completeness_score"],
                quality_issues_count=len(quality_metrics["quality_issues"])
            )
            
            return enriched_data
            
        except Exception as e:
            logger.error(
                "Failed to structure job data",
                url=source_url,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    async def structure_multiple_jobs(
        self, 
        job_contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Structure multiple job contents concurrently.
        
        Args:
            job_contents: List of dictionaries with 'content', 'url', 'source_site'
            
        Returns:
            List of structured job data dictionaries
        """
        logger.info("Starting batch job structuring", total_jobs=len(job_contents))
        
        # Create structuring tasks
        tasks = [
            self.structure_job_data(
                job["content"], 
                job["url"], 
                job["source_site"]
            )
            for job in job_contents
        ]
        
        # Execute tasks with rate limiting
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful structuring
        structured_jobs = []
        errors = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Job structuring failed",
                    url=job_contents[i]["url"],
                    error=str(result)
                )
                errors += 1
            elif result is not None:
                structured_jobs.append(result)
        
        logger.info(
            "Batch job structuring completed",
            total_jobs=len(job_contents),
            successful=len(structured_jobs),
            errors=errors
        )
        
        return structured_jobs
    
    async def test_gemini_extraction(self, test_content: str, test_url: str) -> Dict[str, Any]:
        """
        Test Gemini extraction with sample content.
        
        Args:
            test_content: Sample job content to test with
            test_url: Sample URL for testing
            
        Returns:
            Test results with timing and quality metrics
        """
        logger.info("Testing Gemini extraction", content_length=len(test_content))
        
        start_time = time.time()
        
        try:
            # Test structuring
            result = await self.structure_job_data(test_content, test_url, "test_site")
            
            total_time = time.time() - start_time
            
            test_results = {
                "success": result is not None,
                "processing_time_seconds": total_time,
                "structured_data": result,
                "quality_metrics": {
                    "has_title": bool(result and result.get("title")),
                    "has_company": bool(result and result.get("company")),
                    "has_location": bool(result and result.get("location")),
                    "has_description": bool(result and result.get("description")),
                    "has_missions": bool(result and result.get("missions")),
                    "missions_count": len(result.get("missions", [])) if result else 0,
                    "skills_count": len(result.get("required_skills", [])) if result else 0
                }
            }
            
            logger.info(
                "Gemini extraction test completed",
                success=test_results["success"],
                processing_time=f"{total_time:.2f}s",
                quality_score=sum(test_results["quality_metrics"].values())
            )
            
            return test_results
            
        except Exception as e:
            logger.error("Gemini extraction test failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    async def structure_job_data_expert(
        self,
        expert_prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> Optional[Dict[str, Any]]:
        """
        Structure job data using expert prompt for Phase 2 Enhanced Pipeline.
        This method is specifically designed for Stage 2 processing with comprehensive
        JSON structuration.
        
        Args:
            expert_prompt: Pre-built expert prompt with comprehensive instructions
            model: Gemini model to use
            temperature: Generation temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Comprehensive structured job data dictionary or None if failed
        """
        try:
            logger.info("Starting expert job data structuration",
                       prompt_length=len(expert_prompt),
                       model=model,
                       temperature=temperature)
            
            start_time = time.time()
            
            # Create model with expert configuration
            expert_model = genai.GenerativeModel(
                model_name=model,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json"
                )
            )
            
            # Enforce rate limiting
            await self._enforce_rate_limit()
            
            # Generate structured content
            response = await asyncio.wait_for(
                asyncio.to_thread(expert_model.generate_content, expert_prompt),
                timeout=90.0  # Longer timeout for expert processing
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if not response.text:
                logger.warning("Empty response from Gemini expert")
                return None
            
            # Parse JSON response with enhanced error handling
            try:
                structured_data = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse expert JSON response, attempting cleanup",
                             response_preview=response.text[:300],
                             error=str(e))
                
                # Enhanced JSON cleanup for expert responses
                cleaned_response = self._clean_expert_json_response(response.text)
                try:
                    structured_data = json.loads(cleaned_response)
                    logger.info("Successfully parsed cleaned expert JSON response")
                except json.JSONDecodeError:
                    logger.error("Failed to parse even cleaned expert JSON response",
                               cleaned_preview=cleaned_response[:300])
                    return None
            
            # Validate expert structured data
            if not self._validate_expert_structured_data(structured_data):
                logger.warning("Expert structured data validation failed")
                return None
            
            logger.info("Expert job data structuration completed successfully",
                       processing_time_ms=processing_time,
                       has_title=bool(structured_data.get("title")),
                       has_company=bool(structured_data.get("company")),
                       has_location=bool(structured_data.get("location")),
                       has_salary=bool(structured_data.get("salary")),
                       has_requirements=bool(structured_data.get("requirements")))
            
            return structured_data
            
        except Exception as e:
            logger.error("Expert job data structuration failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    def _clean_expert_json_response(self, response_text: str) -> str:
        """
        Enhanced JSON cleaning for expert responses with complex nested structures.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Cleaned JSON string
        """
        import re
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Remove any explanatory text before JSON
        first_brace = cleaned.find('{')
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        # Remove any text after the last }
        last_brace = cleaned.rfind('}')
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        # Fix common JSON issues in expert responses
        cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas in objects
        cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas in arrays
        
        # Fix quotes issues
        cleaned = re.sub(r'([{,]\s*)"([^"]+)"\s*:', r'\1"\2":', cleaned)  # Normalize key quotes
        
        # Fix null values
        cleaned = re.sub(r':\s*null\s*([,}])', r': null\1', cleaned)
        
        return cleaned.strip()
    
    def _validate_expert_structured_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate expert structured data for Phase 2 Enhanced Pipeline.
        
        Args:
            data: Structured data from expert prompt
            
        Returns:
            True if data meets expert validation criteria
        """
        try:
            # Check that it's a dictionary
            if not isinstance(data, dict):
                logger.warning("Expert data is not a dictionary")
                return False
            
            # Check required fields for expert extraction
            required_fields = ["title", "company"]
            for field in required_fields:
                if field not in data or not data[field]:
                    logger.warning(f"Missing required expert field: {field}")
                    return False
            
            # Validate nested structures if present
            nested_objects = ["location", "contract", "salary", "requirements", "description", "application", "metadata"]
            for field in nested_objects:
                if field in data and data[field] is not None:
                    if not isinstance(data[field], dict):
                        logger.warning(f"Expert field {field} should be a dictionary")
                        return False
            
            # Validate specific nested structures
            if "location" in data and data["location"]:
                location = data["location"]
                if "country" in location and location["country"] and location["country"] != "Togo":
                    logger.info(f"Non-Togo location detected: {location['country']}")
            
            if "salary" in data and data["salary"]:
                salary = data["salary"]
                if "currency" in salary and salary["currency"]:
                    valid_currencies = ["XOF", "EUR", "USD"]
                    if salary["currency"] not in valid_currencies:
                        logger.warning(f"Invalid currency: {salary['currency']}")
            
            return True
            
        except Exception as e:
            logger.error("Expert data validation failed", error=str(e))
            return False

    def validate_structured_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate structured job data against schema.
        
        Args:
            data: Structured job data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not data.get("title") or not data.get("company"):
                return False
            
            # Check data types
            string_fields = ["title", "company", "location", "contract_type", 
                           "salary_range", "experience_level", "education_level", 
                           "sector", "description", "profile"]
            
            for field in string_fields:
                if field in data and data[field] is not None:
                    if not isinstance(data[field], str):
                        return False
            
            # Check array fields
            array_fields = ["missions", "required_skills"]
            for field in array_fields:
                if field in data and data[field] is not None:
                    if not isinstance(data[field], list):
                        return False
                    # Check that all items are strings
                    if not all(isinstance(item, str) for item in data[field]):
                        return False
            
            return True
            
        except Exception as e:
            logger.error("Data validation failed", error=str(e))
            return False