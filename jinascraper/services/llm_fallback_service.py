"""
Service de fallback multi-LLM avec rotation automatique des clés API.

Ce service implémente une stratégie de fallback robuste :
1. Rotation des clés API Gemini (plusieurs comptes)
2. Fallback vers d'autres LLM gratuits (OpenRouter, Groq, etc.)
3. Gestion intelligente des erreurs (quota vs autres)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
import time
import random

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Types de providers LLM supportés."""
    GEMINI = "gemini"
    OPENROUTER_DEEPSEEK = "openrouter_deepseek"
    OPENROUTER_QWEN = "openrouter_qwen"
    OPENROUTER_LLAMA = "openrouter_llama"
    GROQ = "groq"
    GOOGLE_AI_STUDIO = "google_ai_studio"
    CEREBRAS = "cerebras"


class ErrorType(str, Enum):
    """Types d'erreurs pour la logique de fallback."""
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class LLMConfig:
    """Configuration pour un provider LLM."""
    provider: LLMProvider
    api_keys: List[str]
    base_url: str
    model_name: str
    max_requests_per_day: int
    max_requests_per_minute: int
    priority: int  # Plus bas = plus prioritaire


@dataclass
class LLMAttempt:
    """Résultat d'une tentative d'appel LLM."""
    provider: LLMProvider
    api_key_index: int
    success: bool
    error_type: Optional[ErrorType]
    response: Optional[Dict[str, Any]]
    processing_time_ms: int


class LLMFallbackService:
    """
    Service de fallback multi-LLM avec rotation automatique.
    
    Stratégie :
    1. Essaie les clés Gemini en rotation
    2. Si toutes les clés Gemini échouent avec quota, passe aux autres LLM
    3. Essaie les autres LLM par ordre de priorité
    4. Retourne la première réponse réussie
    """
    
    def __init__(self):
        self.providers_config = self._initialize_providers()
        self.current_key_indices = {provider: 0 for provider in LLMProvider}
        self.failed_keys_cooldown = {}  # Cooldown pour les clés qui ont échoué
        
    def _initialize_providers(self) -> Dict[LLMProvider, LLMConfig]:
        """Initialise la configuration des providers LLM."""
        import os
        
        # Charger les vraies clés API depuis l'environnement
        gemini_keys = []
        for key_name in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
            key_value = os.getenv(key_name)
            if key_value:
                gemini_keys.append(key_value)
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        google_ai_studio_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        
        return {
            LLMProvider.OPENROUTER_DEEPSEEK: LLMConfig(
                provider=LLMProvider.OPENROUTER_DEEPSEEK,
                api_keys=[openrouter_key] if openrouter_key else [],
                base_url="https://openrouter.ai/api/v1",
                model_name="deepseek/deepseek-r1:free",  # Modèle de raisonnement avancé
                max_requests_per_day=50,
                max_requests_per_minute=20,
                priority=1  # Priorité la plus haute - OpenRouter en premier !
            ),
            
            LLMProvider.GEMINI: LLMConfig(
                provider=LLMProvider.GEMINI,
                api_keys=gemini_keys,
                base_url="https://generativelanguage.googleapis.com/v1beta",
                model_name="gemini-1.5-flash",
                max_requests_per_day=50,  # Free tier
                max_requests_per_minute=15,
                priority=2  # Gemini en deuxième
            ),
            
            LLMProvider.OPENROUTER_QWEN: LLMConfig(
                provider=LLMProvider.OPENROUTER_QWEN,
                api_keys=[openrouter_key] if openrouter_key else [],
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwen3-coder:free",  # Spécialisé code/JSON, classé #7
                max_requests_per_day=50,
                max_requests_per_minute=20,
                priority=3
            ),
            
            LLMProvider.OPENROUTER_LLAMA: LLMConfig(
                provider=LLMProvider.OPENROUTER_LLAMA,
                api_keys=[openrouter_key] if openrouter_key else [],
                base_url="https://openrouter.ai/api/v1",
                model_name="meta-llama/llama-4-maverick:free",  # Dernière version Llama
                max_requests_per_day=50,
                max_requests_per_minute=20,
                priority=4
            ),
            
            LLMProvider.GROQ: LLMConfig(
                provider=LLMProvider.GROQ,
                api_keys=[groq_key] if groq_key else [],
                base_url="https://api.groq.com/openai/v1",
                model_name="llama-3.3-70b-versatile",
                max_requests_per_day=14400,
                max_requests_per_minute=30,
                priority=5
            ),
            
            LLMProvider.GOOGLE_AI_STUDIO: LLMConfig(
                provider=LLMProvider.GOOGLE_AI_STUDIO,
                api_keys=[google_ai_studio_key] if google_ai_studio_key else [],
                base_url="https://generativelanguage.googleapis.com/v1beta",
                model_name="gemini-2.5-flash",
                max_requests_per_day=250,
                max_requests_per_minute=10,
                priority=6
            ),
            
            LLMProvider.CEREBRAS: LLMConfig(
                provider=LLMProvider.CEREBRAS,
                api_keys=[cerebras_key] if cerebras_key else [],
                base_url="https://api.cerebras.ai/v1",
                model_name="llama3.3-70b",
                max_requests_per_day=14400,
                max_requests_per_minute=30,
                priority=7
            )
        }
    
    async def structure_job_data(self, content: str, source_url: str) -> Dict[str, Any]:
        """
        Structure les données d'emploi avec fallback automatique.
        
        Args:
            content: Contenu markdown à structurer
            source_url: URL source de l'offre
            
        Returns:
            Données structurées ou None si tous les providers échouent
        """
        # Trier les providers par priorité
        sorted_providers = sorted(
            self.providers_config.values(), 
            key=lambda x: x.priority
        )
        
        attempts = []
        
        logger.info(f"🚀 Starting LLM fallback with {len(sorted_providers)} providers")
        for i, provider in enumerate(sorted_providers):
            logger.info(f"   {i+1}. {provider.provider.value} (priority {provider.priority}) - {len(provider.api_keys)} keys")
        
        for provider_config in sorted_providers:
            logger.info(f"🧪 Trying provider: {provider_config.provider.value} with {len(provider_config.api_keys)} keys")
            # Vérifier si le provider a des clés API
            if not provider_config.api_keys:
                logger.warning(f"⚠️  Provider {provider_config.provider.value} has no API keys, skipping")
                continue
            
            # Essayer toutes les clés API de ce provider
            for key_index in range(len(provider_config.api_keys)):
                logger.info(f"   🔑 Trying key #{key_index} for {provider_config.provider.value}")
                # Rotation des clés
                current_key_index = (
                    self.current_key_indices[provider_config.provider] + key_index
                ) % len(provider_config.api_keys)
                
                # Vérifier si cette clé est en cooldown
                cooldown_key = f"{provider_config.provider}_{current_key_index}"
                if self._is_key_in_cooldown(cooldown_key):
                    logger.info(f"   ⏰ Key #{current_key_index} for {provider_config.provider.value} is in cooldown, skipping")
                    continue
                
                try:
                    start_time = time.time()
                    
                    # Appel au provider spécifique
                    response = await self._call_provider(
                        provider_config, 
                        current_key_index, 
                        content, 
                        source_url
                    )
                    
                    processing_time = int((time.time() - start_time) * 1000)
                    
                    # Succès !
                    attempt = LLMAttempt(
                        provider=provider_config.provider,
                        api_key_index=current_key_index,
                        success=True,
                        error_type=None,
                        response=response,
                        processing_time_ms=processing_time
                    )
                    attempts.append(attempt)
                    
                    # Mettre à jour l'index pour la prochaine fois
                    self.current_key_indices[provider_config.provider] = (
                        current_key_index + 1
                    ) % len(provider_config.api_keys)
                    
                    logger.info(
                        f"LLM fallback success - provider: {provider_config.provider.value}, "
                        f"key_index: {current_key_index}, processing_time_ms: {processing_time}, "
                        f"total_attempts: {len(attempts)}"
                    )
                    
                    return response
                    
                except Exception as e:
                    processing_time = int((time.time() - start_time) * 1000)
                    error_type = self._classify_error(e)
                    
                    attempt = LLMAttempt(
                        provider=provider_config.provider,
                        api_key_index=current_key_index,
                        success=False,
                        error_type=error_type,
                        response=None,
                        processing_time_ms=processing_time
                    )
                    attempts.append(attempt)
                    
                    # Gestion du cooldown selon le type d'erreur
                    if error_type == ErrorType.QUOTA_EXCEEDED:
                        # Cooldown long pour quota dépassé
                        self._set_key_cooldown(cooldown_key, 3600)  # 1 heure
                    elif error_type == ErrorType.RATE_LIMIT:
                        # Cooldown court pour rate limit
                        self._set_key_cooldown(cooldown_key, 300)   # 5 minutes
                    
                    logger.warning(
                        f"LLM fallback attempt failed - provider: {provider_config.provider.value}, "
                        f"key_index: {current_key_index}, error_type: {error_type.value}, "
                        f"error: {str(e)}, processing_time_ms: {processing_time}"
                    )
                    
                    # Si c'est une erreur de quota sur Gemini, passer directement 
                    # aux autres providers
                    if (provider_config.provider == LLMProvider.GEMINI and 
                        error_type == ErrorType.QUOTA_EXCEEDED):
                        logger.info(f"   🚫 Gemini quota exceeded, breaking to next provider")
                        break
        
        # Tous les providers ont échoué
        logger.error(
            f"All LLM providers failed - total_attempts: {len(attempts)}, "
            f"providers_tried: {[a.provider.value for a in attempts]}"
        )
        
        return None
    
    async def _call_provider(
        self, 
        config: LLMConfig, 
        key_index: int, 
        content: str, 
        source_url: str
    ) -> Dict[str, Any]:
        """Appelle un provider LLM spécifique."""
        api_key = config.api_keys[key_index]
        
        if config.provider == LLMProvider.GEMINI:
            return await self._call_gemini(api_key, config.model_name, content, source_url)
        elif config.provider in [LLMProvider.OPENROUTER_DEEPSEEK, LLMProvider.OPENROUTER_QWEN, LLMProvider.OPENROUTER_LLAMA]:
            return await self._call_openrouter(api_key, config.model_name, content, source_url)
        elif config.provider == LLMProvider.GROQ:
            return await self._call_groq(api_key, config.model_name, content, source_url)
        elif config.provider == LLMProvider.GOOGLE_AI_STUDIO:
            return await self._call_google_ai_studio(api_key, config.model_name, content, source_url)
        elif config.provider == LLMProvider.CEREBRAS:
            return await self._call_cerebras(api_key, config.model_name, content, source_url)
        else:
            raise ValueError(f"Provider non supporté: {config.provider}")
    
    async def _call_gemini(self, api_key: str, model: str, content: str, source_url: str) -> Dict[str, Any]:
        """Appel à l'API Gemini (implémentation existante)."""
        # Réutiliser votre implémentation Gemini existante
        from .gemini_service import GeminiService
        
        gemini_service = GeminiService()
        gemini_service.api_key = api_key  # Override de la clé
        
        # Extraire le site source depuis l'URL
        source_site = self._extract_site_from_url(source_url)
        
        return await gemini_service.structure_job_data(content, source_url, source_site)
    
    async def _call_openrouter(self, api_key: str, model: str, content: str, source_url: str) -> Dict[str, Any]:
        """Appel à l'API OpenRouter (compatible OpenAI)."""
        import aiohttp
        
        prompt = self._build_structuring_prompt(content, source_url)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                # Parser la réponse JSON
                import json
                content_json = json.loads(result["choices"][0]["message"]["content"])
                return content_json
    
    async def _call_groq(self, api_key: str, model: str, content: str, source_url: str) -> Dict[str, Any]:
        """Appel à l'API Groq (compatible OpenAI)."""
        import aiohttp
        
        prompt = self._build_structuring_prompt(content, source_url)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                import json
                content_json = json.loads(result["choices"][0]["message"]["content"])
                return content_json
    
    async def _call_google_ai_studio(self, api_key: str, model: str, content: str, source_url: str) -> Dict[str, Any]:
        """Appel à Google AI Studio (même API que Gemini)."""
        from .gemini_service import GeminiService
        
        gemini_service = GeminiService()
        gemini_service.api_key = api_key  # Override de la clé
        
        # Extraire le site source depuis l'URL
        source_site = self._extract_site_from_url(source_url)
        
        return await gemini_service.structure_job_data(content, source_url, source_site)
    
    async def _call_cerebras(self, api_key: str, model: str, content: str, source_url: str) -> Dict[str, Any]:
        """Appel à l'API Cerebras (compatible OpenAI)."""
        import aiohttp
        
        prompt = self._build_structuring_prompt(content, source_url)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                import json
                content_json = json.loads(result["choices"][0]["message"]["content"])
                return content_json
    
    def _build_structuring_prompt(self, content: str, source_url: str) -> str:
        """Construit le prompt de structuration (réutilise votre prompt existant)."""
        return f"""
Analysez cette offre d'emploi et extrayez les informations dans un format JSON structuré.

Contenu de l'offre :
{content}

URL source : {source_url}

Retournez un JSON avec cette structure exacte :
{{
    "title": "titre du poste",
    "company": "nom de l'entreprise",
    "location": "lieu",
    "contract_type": "type de contrat",
    "salary_range": "fourchette salariale",
    "experience_level": "niveau d'expérience requis",
    "education_level": "niveau d'études requis",
    "sector": "secteur d'activité",
    "description": "description du poste",
    "missions": ["mission 1", "mission 2"],
    "required_skills": ["compétence 1", "compétence 2"],
    "profile": "profil recherché",
    "application_deadline": "date limite candidature",
    "posted_date": "date de publication",
    "source_url": "{source_url}",
    "extraction_method": "llm_fallback"
}}

Extrayez uniquement les informations présentes dans le contenu. N'inventez rien.
"""
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classifie le type d'erreur pour la logique de fallback."""
        error_str = str(error).lower()
        
        if "quota" in error_str or "exceeded" in error_str:
            return ErrorType.QUOTA_EXCEEDED
        elif "rate limit" in error_str or "429" in error_str:
            return ErrorType.RATE_LIMIT
        elif "timeout" in error_str:
            return ErrorType.TIMEOUT
        elif "400" in error_str or "401" in error_str or "403" in error_str:
            return ErrorType.API_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def _is_key_in_cooldown(self, cooldown_key: str) -> bool:
        """Vérifie si une clé API est en cooldown."""
        if cooldown_key not in self.failed_keys_cooldown:
            return False
        
        return time.time() < self.failed_keys_cooldown[cooldown_key]
    
    def _set_key_cooldown(self, cooldown_key: str, duration_seconds: int):
        """Met une clé API en cooldown."""
        self.failed_keys_cooldown[cooldown_key] = time.time() + duration_seconds
    
    def _extract_site_from_url(self, url: str) -> str:
        """Extrait le nom du site depuis une URL."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Mapping des domaines vers les noms de sites
            site_mapping = {
                'www.emploi.tg': 'emploi_tg',
                'emploi.tg': 'emploi_tg',
                'anpetogo.com': 'anpetogo',
                'www.anpetogo.com': 'anpetogo',
                'yop.l-frii.com': 'yop_lfrii',
                'www.yop.l-frii.com': 'yop_lfrii',
                'emploitogo.info': 'emploitogo_info',
                'www.emploitogo.info': 'emploitogo_info',
                'tg.linkedin.com': 'linkedin_togo',
                'indeed.tg': 'indeed_togo',
                'www.indeed.tg': 'indeed_togo'
            }
            
            return site_mapping.get(domain, domain.replace('www.', ''))
            
        except Exception:
            return 'unknown'
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service de fallback."""
        status = {
            "providers": {},
            "cooldowns": {}
        }
        
        for provider, config in self.providers_config.items():
            status["providers"][provider.value] = {
                "priority": config.priority,
                "api_keys_count": len(config.api_keys),
                "current_key_index": self.current_key_indices[provider],
                "model": config.model_name,
                "max_requests_per_day": config.max_requests_per_day
            }
        
        # Cooldowns actifs
        current_time = time.time()
        for key, expiry_time in self.failed_keys_cooldown.items():
            if expiry_time > current_time:
                status["cooldowns"][key] = {
                    "expires_in_seconds": int(expiry_time - current_time)
                }
        
        return status