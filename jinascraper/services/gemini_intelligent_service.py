"""
Gemini Intelligent Service - Adaptation dynamique aux données
Implémentation du concept "Gemini Intelligent" pour extraction adaptative
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from jinascraper.config import config

logger = structlog.get_logger(__name__)


class GeminiIntelligentService:
    """
    Service Gemini "Intelligent" qui s'adapte dynamiquement au contenu
    au lieu d'utiliser un schéma JSON prédéfini.
    """
    
    def __init__(self):
        self.api_key = config.gemini_api_key
        self.model_name = config.gemini_model
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model for intelligent extraction
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent extraction
                top_p=0.9,        # Higher for more creative field discovery
                top_k=50,         # Higher for more diverse field extraction
                max_output_tokens=4096,  # More tokens for comprehensive extraction
                response_mime_type="application/json"
            )
        )
        
        # Rate limiting
        self.rate_limit_delay = 1.0
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()
        
        logger.info("GeminiIntelligentService initialized", model=self.model_name)
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting for Gemini API."""
        async with self._request_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    def _create_intelligent_extraction_prompt(self, content: str, source_url: str, source_site: str = None) -> str:
        """
        Crée un prompt "intelligent" qui demande à Gemini de définir lui-même
        la structure JSON selon le contenu disponible.
        """
        
        prompt = f"""Tu es un expert en extraction intelligente de données d'offres d'emploi au Togo. 

🎯 MISSION INTELLIGENTE :
Analyse le contenu suivant et crée une structure JSON ADAPTÉE AU CONTENU DISPONIBLE.
Ne te limite PAS à un schéma prédéfini. Extrais TOUT ce qui est pertinent et disponible.

📋 RÈGLES D'EXTRACTION INTELLIGENTE :
1. ✅ ANALYSE d'abord le contenu pour identifier TOUS les types d'informations disponibles
2. 🧠 CRÉE une structure JSON qui capture TOUTES ces informations
3. 🔍 ADAPTE les noms de champs selon le contenu (pas de champs fixes)
4. 📊 INCLUS des champs spécialisés selon le type d'offre
5. ❌ Ne jamais inventer d'informations non présentes
6. 🎯 Objectif : ZÉRO PERTE D'INFORMATION

🌍 CONTEXTE :
- Source: {source_site or 'Site d\'emploi togolais'}
- URL: {source_url}
- Pays: Togo (Afrique de l'Ouest)
- Monnaie: Franc CFA (XOF)

🔧 ADAPTATION DYNAMIQUE :
- Si c'est un poste technique → inclus compétences techniques détaillées
- Si c'est un poste commercial → inclus objectifs de vente, zones géographiques
- Si c'est un stage → inclus durée, indemnités, encadrement
- Si c'est humanitaire → inclus missions terrain, langues, mobilité
- Si c'est gouvernemental → inclus références, procédures, critères officiels

📝 EXEMPLES DE CHAMPS ADAPTATIFS :
- Poste technique : "technologies_requises", "certifications", "niveau_expertise"
- Poste commercial : "objectifs_vente", "zone_couverture", "commission"
- Stage : "duree_stage", "indemnite_stage", "encadrement_prevu"
- Humanitaire : "zones_intervention", "langues_requises", "mobilite_internationale"
- Gouvernemental : "reference_poste", "procedure_candidature", "criteres_selection"

🎯 STRUCTURE MINIMALE GARANTIE :
- "titre_poste" : string (obligatoire)
- "entreprise_organisation" : string (obligatoire)
- "informations_complementaires" : object (tout le reste organisé logiquement)

CONTENU À ANALYSER :
{content}

🤖 RÉPONSE ATTENDUE :
Retourne un JSON avec une structure INTELLIGENTE et ADAPTÉE au contenu.
Organise les informations de manière logique et hiérarchique.
Utilise des noms de champs DESCRIPTIFS et SPÉCIFIQUES au contenu.

JSON INTELLIGENT :"""
        
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        reraise=True
    )
    async def _make_intelligent_request(self, prompt: str) -> Dict[str, Any]:
        """Make an intelligent request to Gemini API."""
        await self._enforce_rate_limit()
        
        start_time = time.time()
        
        try:
            logger.info("Making intelligent Gemini request", prompt_length=len(prompt))
            
            response = await asyncio.wait_for(
                asyncio.to_thread(self.model.generate_content, prompt),
                timeout=90.0  # Longer timeout for intelligent processing
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if not response.text:
                raise Exception("Empty response from Gemini")
            
            # Parse JSON response with intelligent cleanup
            try:
                structured_data = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse intelligent JSON response, attempting cleanup", 
                             response_preview=response.text[:300], error=str(e))
                
                cleaned_response = self._clean_intelligent_json_response(response.text)
                try:
                    structured_data = json.loads(cleaned_response)
                    logger.info("Successfully parsed cleaned intelligent JSON response")
                except json.JSONDecodeError:
                    logger.error("Failed to parse even cleaned intelligent JSON response")
                    raise Exception(f"Invalid JSON response: {str(e)}")
            
            # Validate intelligent extraction
            if not self._validate_intelligent_extraction(structured_data):
                raise Exception("Intelligent extraction validation failed")
            
            logger.info(
                "Intelligent Gemini request successful",
                processing_time_ms=processing_time,
                response_length=len(response.text),
                field_count=len(structured_data),
                has_required_fields=self._has_minimum_required_fields(structured_data)
            )
            
            return structured_data
            
        except Exception as e:
            logger.error("Intelligent Gemini request failed", error=str(e))
            raise
    
    def _clean_intelligent_json_response(self, response_text: str) -> str:
        """Clean JSON response for intelligent extraction."""
        import re
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Find JSON boundaries
        first_brace = cleaned.find('{')
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        last_brace = cleaned.rfind('}')
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        # Fix common JSON issues
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        return cleaned.strip()
    
    def _validate_intelligent_extraction(self, data: Dict[str, Any]) -> bool:
        """Validate intelligent extraction results."""
        try:
            # Must be a dictionary
            if not isinstance(data, dict):
                return False
            
            # Must have minimum required information
            return self._has_minimum_required_fields(data)
            
        except Exception as e:
            logger.error("Intelligent extraction validation failed", error=str(e))
            return False
    
    def _has_minimum_required_fields(self, data: Dict[str, Any]) -> bool:
        """Check if data has minimum required fields (flexible)."""
        # Look for job title in various possible field names
        title_fields = ["titre_poste", "title", "poste", "intitule_poste", "nom_poste"]
        has_title = any(data.get(field) for field in title_fields)
        
        # Look for company/organization in various possible field names
        company_fields = ["entreprise_organisation", "company", "entreprise", "organisation", "employeur"]
        has_company = any(data.get(field) for field in company_fields)
        
        return has_title and has_company
    
    async def extract_intelligent_job_data(
        self, 
        raw_content: str, 
        source_url: str,
        source_site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract job data using intelligent adaptation to content.
        
        Args:
            raw_content: Raw job content from Jina Reader
            source_url: URL of the job posting
            source_site: Name of the source site
            
        Returns:
            Intelligently structured job data dictionary or None if extraction failed
        """
        try:
            logger.info("Starting intelligent job data extraction", 
                       url=source_url, content_length=len(raw_content))
            
            start_time = time.time()
            
            # Create intelligent extraction prompt
            prompt = self._create_intelligent_extraction_prompt(raw_content, source_url, source_site)
            
            # Get intelligently structured data from Gemini
            structured_data = await self._make_intelligent_request(prompt)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Add metadata to intelligent extraction
            intelligent_data = {
                **structured_data,
                "_metadata": {
                    "source_url": source_url,
                    "source_site": source_site,
                    "extraction_method": "gemini_intelligent",
                    "processing_time_ms": processing_time,
                    "field_count": len(structured_data),
                    "extraction_timestamp": time.time(),
                    "content_length": len(raw_content)
                }
            }
            
            logger.info(
                "Intelligent job data extraction completed",
                url=source_url,
                processing_time_ms=processing_time,
                field_count=len(structured_data),
                has_minimum_fields=self._has_minimum_required_fields(structured_data)
            )
            
            return intelligent_data
            
        except Exception as e:
            logger.error(
                "Intelligent job data extraction failed",
                url=source_url,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    def analyze_extraction_patterns(self, extractions: list) -> Dict[str, Any]:
        """
        Analyze patterns in intelligent extractions to understand
        what types of fields are commonly discovered.
        """
        if not extractions:
            return {"error": "No extractions to analyze"}
        
        field_frequency = {}
        field_types = {}
        nested_structures = {}
        
        for extraction in extractions:
            if not isinstance(extraction, dict):
                continue
                
            # Analyze top-level fields
            for field, value in extraction.items():
                if field.startswith("_"):  # Skip metadata
                    continue
                    
                # Count field frequency
                field_frequency[field] = field_frequency.get(field, 0) + 1
                
                # Analyze field types
                field_type = type(value).__name__
                if field not in field_types:
                    field_types[field] = {}
                field_types[field][field_type] = field_types[field].get(field_type, 0) + 1
                
                # Analyze nested structures
                if isinstance(value, dict):
                    nested_structures[field] = nested_structures.get(field, set())
                    nested_structures[field].update(value.keys())
        
        # Convert sets to lists for JSON serialization
        for field in nested_structures:
            nested_structures[field] = list(nested_structures[field])
        
        analysis = {
            "total_extractions": len(extractions),
            "field_frequency": field_frequency,
            "field_types": field_types,
            "nested_structures": nested_structures,
            "most_common_fields": sorted(field_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
            "analysis_timestamp": time.time()
        }
        
        logger.info("Extraction pattern analysis completed",
                   total_extractions=len(extractions),
                   unique_fields=len(field_frequency),
                   nested_fields=len(nested_structures))
        
        return analysis