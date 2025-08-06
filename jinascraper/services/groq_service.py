"""Groq service for structured job data extraction with multi-model support."""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

try:
    from ..config import config
    from ..models import JobOffer, ExtractionMethod, ExtractionMetadata
except ImportError:
    # Fallback pour imports absolus - méthode robuste
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        from config.settings import config
        from models import JobOffer, ExtractionMethod, ExtractionMetadata
    except ImportError:
        # Fallback ultime avec chemins absolus
        config_path = os.path.join(parent_dir, 'config', 'settings.py')
        models_path = os.path.join(parent_dir, 'models.py')
        
        import importlib.util
        
        # Import config
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        config = config_module.config
        
        # Import models
        spec = importlib.util.spec_from_file_location("models", models_path)
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)
        JobOffer = models_module.JobOffer
        ExtractionMethod = models_module.ExtractionMethod
        ExtractionMetadata = models_module.ExtractionMetadata


logger = structlog.get_logger(__name__)


class GroqError(Exception):
    """Base exception for Groq service errors."""
    pass


class GroqAPIError(GroqError):
    """Exception for Groq API-related errors."""
    pass


class GroqValidationError(GroqError):
    """Exception for Groq response validation errors."""
    pass


class GroqService:
    """Service for structuring job data using Groq AI with multi-model rotation and best practices."""
    
    def __init__(self):
        if AsyncGroq is None:
            raise ImportError("groq package not installed. Install with: pip install groq")
        
        # Configuration des clés API
        self.api_keys = getattr(config, "groq_api_keys", [])
        if not self.api_keys:
            # Fallback vers clé unique
            single_key = getattr(config, "groq_api_key", "")
            self.api_keys = [single_key] if single_key else []
        
        if not self.api_keys:
            raise ValueError("No Groq API key configured. Set GROQ_API_KEY or GROQ_API_KEYS.")
        
        # Configuration des modèles selon la recherche effectuée
        self.models = [
            "llama-3.3-70b-versatile",      # Qualité maximale (1000 req/jour)
            "gemma2-9b-it",                 # Volume élevé (14,400 req/jour)
            "deepseek-r1-distill-llama-70b", # Raisonnement avancé (1000 req/jour)
            "llama-3.1-8b-instant"          # Rapide (14,400 req/jour)
        ]
        
        # État de rotation des clés et modèles
        self._key_index = 0
        self._model_index = 0
        self._key_failures = {k: 0 for k in self.api_keys}
        self._key_cooldown_until = {k: 0.0 for k in self.api_keys}
        self._model_daily_requests = {m: 0 for m in self.models}
        self._last_reset_date = time.strftime("%Y-%m-%d")
        
        # Configuration de cooldown
        self._cooldown_base_seconds = 30.0
        self._max_cooldown_seconds = 600.0
        
        # Client Groq avec la première clé
        self.client = AsyncGroq(api_key=self._current_key())
        
        # Rate limiting local
        self.rate_limit_delay = 1.0  # 1 seconde entre requêtes
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()
        
        logger.info("GroqService initialized", 
                   models=self.models, 
                   keys_configured=len(self.api_keys))
    
    def _current_key(self) -> Optional[str]:
        """Retourne la clé API courante."""
        if not self.api_keys:
            return None
        return self.api_keys[self._key_index % len(self.api_keys)]
    
    def _current_model(self) -> str:
        """Retourne le modèle courant selon la stratégie de rotation."""
        return self.models[self._model_index % len(self.models)]
    
    def _reset_daily_counters_if_needed(self):
        """Reset les compteurs quotidiens si on change de jour."""
        current_date = time.strftime("%Y-%m-%d")
        if current_date != self._last_reset_date:
            self._model_daily_requests = {m: 0 for m in self.models}
            self._last_reset_date = current_date
            logger.info("Daily request counters reset", date=current_date)
    
    def _select_best_model(self) -> str:
        """Sélectionne le meilleur modèle disponible selon les quotas."""
        self._reset_daily_counters_if_needed()
        
        # Limites par modèle (selon la recherche)
        model_limits = {
            "llama-3.3-70b-versatile": 1000,
            "deepseek-r1-distill-llama-70b": 1000,
            "gemma2-9b-it": 14400,
            "llama-3.1-8b-instant": 14400
        }
        
        # Priorité : qualité d'abord, puis volume
        priority_order = [
            "llama-3.3-70b-versatile",      # Meilleure qualité
            "deepseek-r1-distill-llama-70b", # Raisonnement avancé
            "gemma2-9b-it",                 # Volume élevé
            "llama-3.1-8b-instant"          # Fallback rapide
        ]
        
        for model in priority_order:
            if self._model_daily_requests[model] < model_limits[model]:
                return model
        
        # Si tous les quotas sont épuisés, utiliser le modèle avec le plus de marge
        return "gemma2-9b-it"  # Le plus généreux en quotas
    
    async def _enforce_rate_limit(self):
        """Applique le rate limiting client."""
        async with self._request_lock:
            now = time.time()
            dt = now - self._last_request_time
            if dt < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - dt
                logger.debug("Groq rate limiting: sleeping", sleep_seconds=sleep_time)
                await asyncio.sleep(sleep_time)
            self._last_request_time = time.time()
    
    def _get_job_extraction_schema(self) -> Dict[str, Any]:
        """Schéma JSON pour l'extraction de données d'emploi (identique à Gemini)."""
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
        """Crée un prompt optimisé pour l'extraction (réutilise la logique Gemini)."""
        schema = self._get_job_extraction_schema()
        
        # Instructions spécifiques par source (réutilise la logique Gemini)
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
        """Instructions spécialisées par source (identique à Gemini)."""
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
        retry=retry_if_exception_type((GroqAPIError, Exception)),
        reraise=True
    )
    async def _make_groq_request(self, prompt: str) -> Dict[str, Any]:
        """Effectue une requête Groq avec retry et rotation des clés/modèles."""
        await self._enforce_rate_limit()
        start_time = time.time()
        
        # Sélectionner le meilleur modèle disponible
        model = self._select_best_model()
        
        # Essayer avec toutes les clés disponibles
        tried_keys = set()
        last_error: Optional[Exception] = None
        
        for _ in range(len(self.api_keys)):
            key = self._select_viable_key()
            if not key or key in tried_keys:
                break
            tried_keys.add(key)
            
            try:
                logger.info("Making Groq request", 
                           model=model, 
                           prompt_length=len(prompt), 
                           key_index=self._key_index)
                
                # Créer client avec la clé courante
                client = AsyncGroq(api_key=key)
                
                # Requête avec JSON mode (selon les bonnes pratiques Groq)
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},  # JSON Mode natif
                    temperature=0.1,  # Faible pour cohérence
                    max_tokens=2048,
                    timeout=60.0
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                if not response.choices or not response.choices[0].message.content:
                    raise GroqAPIError("Empty response from Groq")
                
                content = response.choices[0].message.content
                
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse Groq JSON response, attempting cleanup",
                                   response_text=content[:200], error=str(e))
                    cleaned_response = self._clean_json_response(content)
                    try:
                        structured_data = json.loads(cleaned_response)
                        logger.info("Successfully parsed cleaned JSON response")
                    except json.JSONDecodeError:
                        logger.error("Failed to parse even cleaned JSON response",
                                     cleaned_response=cleaned_response[:200])
                        raise GroqValidationError(f"Invalid JSON response: {str(e)}")
                
                # Succès : incrémenter le compteur du modèle et reset des échecs
                self._model_daily_requests[model] += 1
                self._key_failures[key] = 0
                self._key_cooldown_until[key] = 0.0
                
                logger.info(
                    "Groq request successful",
                    model=model,
                    processing_time_ms=processing_time,
                    response_length=len(content),
                    has_title=bool(structured_data.get("title")),
                    has_company=bool(structured_data.get("company")),
                    daily_requests=self._model_daily_requests[model]
                )
                return structured_data
            
            except Exception as e:
                last_error = e
                err_text = str(e).lower()
                is_rate = ("rate" in err_text) or ("429" in err_text) or ("quota" in err_text)
                is_server = ("5" in err_text) or ("unavailable" in err_text)
                
                logger.warning("Groq request failed on key, will rotate if possible",
                               model=model, error=str(e), key_tail=key[-6:] if key else None)
                
                # Marquer la clé en échec
                self._mark_key_failure(key, is_rate or is_server)
                
                # Rotation vers la clé suivante
                self._rotate_key()
        
        # Si aucune clé n'a réussi
        if last_error:
            if isinstance(last_error, GroqError):
                raise last_error
            raise GroqError(f"All Groq keys failed: {str(last_error)}")
        raise GroqError("No Groq key available to make request")
    
    def _clean_json_response(self, response_text: str) -> str:
        """Nettoie les réponses JSON avec des problèmes de formatage."""
        import re
        
        # Supprimer les blocs de code markdown
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Trouver le premier { et le dernier }
        first_brace = cleaned.find('{')
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        last_brace = cleaned.rfind('}')
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        # Corriger les problèmes JSON courants
        cleaned = re.sub(r',\s*}', '}', cleaned)  # Virgules finales
        cleaned = re.sub(r',\s*]', ']', cleaned)  # Virgules finales dans arrays
        
        return cleaned.strip()
    
    def _select_viable_key(self) -> Optional[str]:
        """Sélectionne une clé non en cooldown."""
        now = time.time()
        for i in range(len(self.api_keys)):
            idx = (self._key_index + i) % len(self.api_keys)
            key = self.api_keys[idx]
            if now >= self._key_cooldown_until.get(key, 0.0):
                self._key_index = idx
                return key
        return None
    
    def _rotate_key(self):
        """Rotation vers la clé suivante."""
        if not self.api_keys:
            return
        self._key_index = (self._key_index + 1) % len(self.api_keys)
    
    def _mark_key_failure(self, key: Optional[str], backoffable: bool):
        """Marque une clé en échec avec cooldown exponentiel."""
        if not key:
            return
        self._key_failures[key] = self._key_failures.get(key, 0) + 1
        if backoffable:
            cooldown = min(
                self._cooldown_base_seconds * (2 ** (self._key_failures[key] - 1)), 
                self._max_cooldown_seconds
            )
            self._key_cooldown_until[key] = time.time() + cooldown
            logger.info("Applying cooldown to Groq key", 
                       cooldown_seconds=cooldown, 
                       failures=self._key_failures[key])
    
    def _validate_extraction_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et score la qualité des données extraites (identique à Gemini)."""
        quality_metrics = {
            "completeness_score": 0.0,
            "quality_issues": [],
            "field_coverage": {}
        }
        
        # Champs requis
        required_fields = ["title", "company"]
        for field in required_fields:
            if data.get(field):
                quality_metrics["completeness_score"] += 0.3
                quality_metrics["field_coverage"][field] = True
            else:
                quality_metrics["quality_issues"].append(f"Missing required field: {field}")
                quality_metrics["field_coverage"][field] = False
        
        # Champs optionnels importants
        important_fields = ["location", "description", "missions", "required_skills"]
        for field in important_fields:
            if data.get(field):
                quality_metrics["completeness_score"] += 0.1
                quality_metrics["field_coverage"][field] = True
            else:
                quality_metrics["field_coverage"][field] = False
        
        # Vérifications de qualité
        if data.get("title") and len(data["title"]) < 5:
            quality_metrics["quality_issues"].append("Title too short")
        
        if data.get("company") and len(data["company"]) < 2:
            quality_metrics["quality_issues"].append("Company name too short")
        
        if data.get("missions") and isinstance(data["missions"], list):
            if len(data["missions"]) == 0:
                quality_metrics["quality_issues"].append("Empty missions list")
            elif len(data["missions"]) > 10:
                quality_metrics["quality_issues"].append("Too many missions (possible parsing error)")
        
        # Plafonner le score à 1.0
        quality_metrics["completeness_score"] = min(quality_metrics["completeness_score"], 1.0)
        
        return quality_metrics

    async def structure_job_data(
        self, 
        raw_content: str, 
        source_url: str,
        source_site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Structure les données d'emploi brutes en format standardisé avec Groq.
        
        Args:
            raw_content: Contenu brut de l'offre d'emploi
            source_url: URL de l'offre d'emploi
            source_site: Nom du site source
            
        Returns:
            Dictionnaire de données d'emploi structurées ou None si échec
        """
        try:
            logger.info("Structuring job data with Groq", 
                       url=source_url, content_length=len(raw_content))
            
            start_time = time.time()
            
            # Créer le prompt d'extraction optimisé
            prompt = self._create_extraction_prompt(raw_content, source_url, source_site)
            
            # Obtenir les données structurées de Groq
            structured_data = await self._make_groq_request(prompt)
            
            # Valider la qualité de l'extraction
            quality_metrics = self._validate_extraction_quality(structured_data)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Vérifier la qualité de l'extraction
            if quality_metrics["completeness_score"] < 0.4:  # Seuil minimum 40%
                logger.warning("Low quality extraction",
                             completeness_score=quality_metrics["completeness_score"],
                             issues=quality_metrics["quality_issues"])
                return None
            
            # Ajouter les métadonnées
            metadata = ExtractionMetadata(
                method=ExtractionMethod.GROQ,
                source_site=source_site,
                processing_time_ms=processing_time
            )
            
            # Enrichir avec métadonnées et informations de qualité
            enriched_data = {
                **structured_data,
                "source_url": source_url,
                "extraction_method": ExtractionMethod.GROQ,
                "extraction_metadata": metadata.dict(),
                "quality_metrics": quality_metrics,
                "raw_data": {"content": raw_content}
            }
            
            logger.info(
                "Job data structured successfully with Groq",
                url=source_url,
                processing_time_ms=processing_time,
                title=structured_data.get("title", "")[:50],
                company=structured_data.get("company", "")[:30],
                completeness_score=quality_metrics["completeness_score"],
                quality_issues_count=len(quality_metrics["quality_issues"]),
                model_used=self._select_best_model()
            )
            
            return enriched_data
            
        except Exception as e:
            logger.error(
                "Failed to structure job data with Groq",
                url=source_url,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    async def test_groq_extraction(self, test_content: str, test_url: str) -> Dict[str, Any]:
        """
        Test l'extraction Groq avec du contenu d'exemple.
        
        Args:
            test_content: Contenu d'exemple pour le test
            test_url: URL d'exemple pour le test
            
        Returns:
            Résultats du test avec timing et métriques de qualité
        """
        logger.info("Testing Groq extraction", content_length=len(test_content))
        
        start_time = time.time()
        
        try:
            # Test de structuration
            result = await self.structure_job_data(test_content, test_url, "test_site")
            
            total_time = time.time() - start_time
            
            test_results = {
                "success": result is not None,
                "processing_time_seconds": total_time,
                "structured_data": result,
                "model_used": self._select_best_model(),
                "daily_requests_used": dict(self._model_daily_requests),
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
                "Groq extraction test completed",
                success=test_results["success"],
                processing_time=f"{total_time:.2f}s",
                model_used=test_results["model_used"],
                quality_score=sum(test_results["quality_metrics"].values())
            )
            
            return test_results
            
        except Exception as e:
            logger.error("Groq extraction test failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": time.time() - start_time,
                "model_attempted": self._select_best_model()
            }