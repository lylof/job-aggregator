"""
Service Gemini amélioré avec système de fallback multi-LLM.

Ce service remplace le GeminiService standard et ajoute :
1. Rotation automatique des clés API Gemini
2. Fallback vers d'autres LLM gratuits
3. Gestion intelligente des erreurs
"""

import os
import logging
from typing import Dict, Any, Optional
import structlog

from .llm_fallback_service import LLMFallbackService, LLMProvider
from .gemini_service import GeminiService, GeminiError

logger = structlog.get_logger(__name__)


class EnhancedGeminiService:
    """
    Service Gemini avec fallback automatique vers d'autres LLM.
    
    Utilise le LLMFallbackService pour gérer :
    - Rotation des clés API Gemini
    - Fallback vers OpenRouter, Groq, etc.
    - Gestion des quotas et rate limits
    """
    
    def __init__(self):
        # Initialiser le service de fallback
        self.fallback_service = LLMFallbackService()
        
        # Charger les clés API depuis l'environnement
        self._load_api_keys()
        
        logger.info(
            "Enhanced Gemini service initialized",
            providers_count=len(self.fallback_service.providers_config),
            gemini_keys_count=len(self.fallback_service.providers_config[LLMProvider.GEMINI].api_keys)
        )
    
    def _load_api_keys(self):
        """Charge les clés API depuis les variables d'environnement."""
        # Clés Gemini multiples
        gemini_keys = []
        for i in range(1, 10):  # Support jusqu'à 9 clés
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                gemini_keys.append(key)
        
        # Fallback vers l'ancienne variable si aucune nouvelle clé
        if not gemini_keys:
            old_key = os.getenv("GEMINI_API_KEY")
            if old_key:
                gemini_keys.append(old_key)
        
        if gemini_keys:
            self.fallback_service.providers_config[LLMProvider.GEMINI].api_keys = gemini_keys
        
        # Autres clés API
        api_key_mapping = {
            LLMProvider.OPENROUTER_DEEPSEEK: "OPENROUTER_API_KEY",
            LLMProvider.OPENROUTER_QWEN: "OPENROUTER_API_KEY", 
            LLMProvider.OPENROUTER_LLAMA: "OPENROUTER_API_KEY",
            LLMProvider.GROQ: "GROQ_API_KEY", 
            LLMProvider.GOOGLE_AI_STUDIO: "GOOGLE_AI_STUDIO_API_KEY",
            LLMProvider.CEREBRAS: "CEREBRAS_API_KEY"
        }
        
        for provider, env_var in api_key_mapping.items():
            key = os.getenv(env_var)
            if key:
                self.fallback_service.providers_config[provider].api_keys = [key]
            else:
                # Désactiver le provider si pas de clé
                logger.warning(f"No API key found for {provider.value}, provider disabled")
                self.fallback_service.providers_config[provider].api_keys = []
    
    async def structure_job_data(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """
        Structure les données d'emploi avec fallback automatique.
        
        Args:
            content: Contenu markdown de l'offre d'emploi
            source_url: URL source de l'offre
            
        Returns:
            Données structurées ou None si tous les providers échouent
        """
        logger.info(
            "Starting job data structuring with fallback",
            content_length=len(content),
            source_url=source_url
        )
        
        try:
            # Utiliser le service de fallback
            result = await self.fallback_service.structure_job_data(content, source_url)
            
            if result:
                logger.info(
                    "Job data structured successfully with fallback",
                    source_url=source_url,
                    has_title=bool(result.get("title")),
                    has_company=bool(result.get("company")),
                    extraction_method=result.get("extraction_method", "unknown")
                )
                
                # Ajouter les métadonnées d'extraction
                result["extraction_metadata"] = {
                    "method": "llm_fallback",
                    "extracted_at": time.time(),
                    "source_site": self._extract_site_from_url(source_url),
                    "confidence_score": None,
                    "enriched_fields": [],
                    "processing_time_ms": None  # Sera ajouté par le fallback service
                }
                
                return result
            else:
                logger.error(
                    "All LLM providers failed to structure job data",
                    source_url=source_url,
                    content_length=len(content)
                )
                return None
                
        except Exception as e:
            logger.error(
                "Unexpected error in enhanced Gemini service",
                error=str(e),
                source_url=source_url,
                exc_info=True
            )
            return None
    
    def _extract_site_from_url(self, url: str) -> str:
        """Extrait le nom du site depuis l'URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Mapping des domaines vers les noms de sites
            site_mapping = {
                "www.emploi.tg": "emploi_tg",
                "emploi.tg": "emploi_tg",
                "yop.l-frii.com": "yop_lfrii",
                "www.anpetogo.org": "anpetogo",
                "anpetogo.org": "anpetogo",
                "tg.linkedin.com": "linkedin_togo",
                "tg.indeed.com": "indeed_togo",
                "www.emploitogo.info": "emploitogo_info",
                "emploitogo.info": "emploitogo_info"
            }
            
            return site_mapping.get(domain, domain)
            
        except Exception:
            return "unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service avec informations de fallback."""
        fallback_status = self.fallback_service.get_status()
        
        return {
            "service": "enhanced_gemini_with_fallback",
            "providers": fallback_status["providers"],
            "active_cooldowns": len(fallback_status["cooldowns"]),
            "cooldowns": fallback_status["cooldowns"]
        }
    
    # Méthodes de compatibilité avec l'ancien GeminiService
    async def enrich_job_data(self, content: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Alias pour structure_job_data (compatibilité)."""
        return await self.structure_job_data(content, source_url)


# Factory function pour faciliter la migration
def create_gemini_service() -> EnhancedGeminiService:
    """Crée une instance du service Gemini amélioré."""
    return EnhancedGeminiService()