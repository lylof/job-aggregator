"""
Service OpenRouter pour l'enrichissement IA des données d'emploi
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class OpenRouterService:
    """
    Service pour l'enrichissement des données d'emploi via OpenRouter API.
    Supporte la rotation multi-clés et backoff exponentiel simple.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek/deepseek-r1:free"):
        from jinascraper.config import config
        # Charger clés: paramètre direct > liste env > clé unique env
        keys_env = getattr(config, "openrouter_api_keys", [])
        if api_key:
            self.api_keys = [api_key]
        elif keys_env:
            self.api_keys = [k for k in keys_env if k]
        else:
            single = os.getenv("OPENROUTER_API_KEY")
            self.api_keys = [single] if single else []
        if not self.api_keys:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEYS or OPENROUTER_API_KEY.")
        
        # Modèles et configuration HTTP OpenRouter
        self.model = model or getattr(config, "openrouter_default_model", "deepseek/deepseek-r1:free")
        self.preferred_models = getattr(config, "openrouter_preferred_models", [self.model])
        self.http_referer = getattr(config, "openrouter_http_referer", "https://localhost/")
        self.x_title = getattr(config, "openrouter_x_title", "JinaScraper Backend")
        self.base_url = "https://openrouter.ai/api/v1"
        
        # État de rotation et cooldown
        self._key_index = 0
        self._key_failures = {k: 0 for k in self.api_keys}
        self._key_cooldown_until = {k: 0.0 for k in self.api_keys}
        self._cooldown_base_seconds = 30.0
        self._max_cooldown_seconds = 600.0
        
        # Rate limit client léger
        self._rate_delay = 0.5
        self._last_ts = 0.0
        self._lock = asyncio.Lock()
        
        logger.info("OpenRouterService initialized", model=self.model, keys_configured=len(self.api_keys), preferred_models=self.preferred_models, http_referer=self.http_referer, x_title=self.x_title)
    
    async def structure_job_data(self, content: str, source_url: str, source_site: str) -> Dict[str, Any]:
        """
        Structure les données d'emploi extraites en utilisant OpenRouter.
        Aligne STRICTEMENT le contenu du prompt sur celui utilisé par Groq/Gemini.
        """
        logger.info("Structuring job data with OpenRouter", content_length=len(content), url=source_url)

        try:
            # Construire le prompt 100% aligné Groq/Gemini (même contenu)
            prompt = self._build_llm_aligned_prompt(content, source_url, source_site)

            # Faire l'appel à l'API OpenRouter
            result = await self._make_openrouter_request(prompt)

            # Ajouter les métadonnées d'extraction
            result["extraction_metadata"] = {
                "method": "openrouter",
                "provider_used": "openrouter",
                "source_site": source_site,
                "extracted_at": asyncio.get_event_loop().time(),
                "confidence_score": None,
                "enriched_fields": list(result.keys()),
                "processing_time_ms": None  # Sera calculé par l'appelant
            }

            logger.info("Job data structured successfully with OpenRouter", url=source_url, fields_extracted=len(result))

            return result

        except Exception as e:
            logger.error("Failed to structure job data with OpenRouter", error=str(e), url=source_url)
            raise
    
    def _build_llm_aligned_prompt(self, content: str, source_url: str, source_site: str) -> str:
        """
        Construit un message utilisateur STRICTEMENT aligné au prompt Groq/Gemini.
        - Retour JSON uniquement
        - Utiliser null pour champs absents, [] pour listes
        - Fidélité stricte au texte source
        - Inclure content et source_url
        Remarque: on conserve une seule variante unifiée pour garantir l'identité de contenu.
        """
        return (
            "Analyse cette offre d'emploi et retourne UNIQUEMENT un JSON valide, sans texte additionnel.\n"
            "Règles STRICTES:\n"
            "1) Reproduis fidèlement les informations du texte source (pas de reformulation).\n"
            "2) Utilise null pour les champs absents et [] pour les listes vides.\n"
            "3) Respecte les champs standards suivants (ajoute seulement s'ils sont présents):\n"
            "{\n"
            '  "title": "titre exact du poste",\n'
            '  "company": "nom exact de l\'entreprise",\n'
            '  "location": "ville/région exactes",\n'
            '  "contract_type": "type de contrat (CDI, CDD, Stage, etc.)",\n'
            '  "salary_range": "fourchette salariale si mentionnée",\n'
            '  "description": "description exacte du poste",\n'
            '  "requirements": "exigences/qualifications exactes si présentes",\n'
            '  "benefits": "avantages si présents",\n'
            '  "application_deadline": "date limite si mentionnée",\n'
            '  "experience_level": "niveau d\'expérience",\n'
            '  "education_level": "niveau d\'études",\n'
            '  "skills": ["compétence1", "compétence2"],\n'
            '  "languages": ["langue1", "langue2"],\n'
            '  "remote_work": true/false/null,\n'
            '  "source_url": "reprends exactement l\'URL source",\n'
            '  "extraction_method": "openrouter"\n'
            "}\n"
            "Contenu de l'offre:\n"
            f"{content}\n\n"
            f"URL SOURCE: {source_url}\n"
            "Retourne uniquement le JSON:"
        )
    
    def _build_emploitg_prompt(self, content: str, source_url: str) -> str:
        """Prompt spécialisé pour emploi.tg basé sur le schéma JSON standard."""
        
        return f"""
EXTRACTION EMPLOI.TG - RÈGLES STRICTES :

1. EXTRAIRE EXACTEMENT le texte présent, SANS réécriture ni reformulation
2. RESPECTER la structure JSON standard emploi.tg définie ci-dessous
3. UTILISER null pour les champs absents, [] pour les listes vides
4. IDENTIFIER les sections par leurs titres exacts : "Résumé du poste", "Entreprise", "Détails de l'annonce", "Profil recherché", "Critères de l'annonce"
5. CONSERVER toutes les URLs et liens exacts
6. SÉPARER les listes selon les délimiteurs du site (" - ", puces, etc.)

STRUCTURE JSON EMPLOI.TG STANDARD :

{{
  "metadata": {{
    "published_time": "extraire Published Time si présent, sinon null",
    "source_site": "emploi_tg",
    "extraction_method": "openrouter"
  }},
  
  "job_summary": {{
    "title": "titre exact du poste depuis 'Poste proposé :'",
    "sectors": ["secteurs depuis Résumé du poste, séparés par -"],
    "location": "ville exacte depuis Résumé du poste",
    "experience_levels": ["niveaux d'expérience exacts, séparés par -"],
    "education_levels": ["niveaux d'études exacts, séparés par -"],
    "contract_types": ["types de contrat exacts"]
  }},
  
  "company": {{
    "name": "nom exact de l'entreprise depuis section Entreprise",
    "profile_url": "URL du profil recruteur si présente",
    "activity_sectors": ["secteurs d'activité exacts depuis 'Secteur d'activité'"],
    "website": "Site Internet si présent",
    "job_listings_url": "URL 'Voir toutes nos annonces' si présente",
    "description": "Description de l'entreprise exacte",
    "logo_url": "URL du logo si présente"
  }},
  
  "job_details": {{
    "position_title": "titre exact depuis 'Poste proposé :'",
    "description": "description complète du poste depuis Détails de l'annonce",
    "responsibilities": ["liste des responsabilités/missions si présentes"],
    "benefits": ["avantages offerts si mentionnés"]
  }},
  
  "required_profile": {{
    "qualifications": ["qualifications depuis Profil recherché"],
    "education_training": ["formations requises"],
    "experience": "expérience requise exacte",
    "technical_skills": ["compétences techniques"],
    "soft_skills": ["qualités personnelles"]
  }},
  
  "job_criteria": {{
    "sectors": ["métiers depuis Critères de l'annonce"],
    "activity_sectors": ["secteurs d'activité depuis Critères"],
    "contract_type": "Type de contrat exact",
    "region": "Région exacte",
    "city": "Ville exacte",
    "remote_work": "Travail à distance si mentionné, sinon null",
    "experience_level": ["Niveau d'expérience exact"],
    "education_level": ["Niveau d'études exact"],
    "required_languages": [
      {{
        "language": "langue",
        "level": "niveau"
      }}
    ],
    "positions_available": "Nombre de poste(s) si mentionné",
    "team_management": "Management d'équipe si mentionné"
  }},
  
  "skills_keywords": ["mots-clés/compétences listés à la fin"],
  
  "application": {{
    "application_urls": ["URLs de candidature exactes"],
    "application_method": "méthode de candidature"
  }}
}}

CONTENU DE L'OFFRE EMPLOI.TG :
{content}

URL SOURCE : {source_url}

RETOURNEZ UNIQUEMENT LE JSON STRUCTURÉ, SANS TEXTE SUPPLÉMENTAIRE :
"""
    
    def _build_generic_prompt(self, content: str, source_url: str, source_site: str) -> str:
        """Prompt générique pour les autres sources."""
        
        return f"""
Analysez cette offre d'emploi et retournez un JSON structuré avec ces champs exacts :

{{
    "title": "titre exact du poste",
    "company": "nom exact de l'entreprise", 
    "location": "lieu de travail (ville, région)",
    "job_type": "type de contrat (CDI, CDD, Stage, etc.)",
    "salary_range": "fourchette salariale si mentionnée, sinon null",
    "description": "description détaillée du poste",
    "requirements": "exigences et qualifications requises",
    "benefits": "avantages et bénéfices offerts",
    "application_deadline": "date limite de candidature si mentionnée",
    "experience_level": "niveau d'expérience requis",
    "education_level": "niveau d'éducation requis",
    "skills": ["compétence1", "compétence2", "compétence3"],
    "languages": ["langue1", "langue2"] si mentionnées,
    "remote_work": true/false si le télétravail est possible,
    "contact_info": "informations de contact si disponibles"
}}

RÈGLES IMPORTANTES :
1. Retournez UNIQUEMENT le JSON, sans texte supplémentaire
2. Utilisez null pour les champs non disponibles
3. Soyez précis et fidèle au contenu original
4. Extrayez toutes les informations disponibles
5. Les skills doivent être une liste de chaînes
6. Les languages doivent être une liste de chaînes

CONTENU DE L'OFFRE :
{content}

URL SOURCE : {source_url}
SITE SOURCE : {source_site}

JSON STRUCTURÉ :
"""
    
    async def _make_openrouter_request(self, prompt: str) -> Dict[str, Any]:
        """Fait l'appel à l'API OpenRouter avec rotation multi-clés et backoff."""
        await self._enforce_rate_limit()
        logger.info("Making OpenRouter request", prompt_length=len(prompt))
        
        last_error: Optional[Exception] = None
        tried = set()
        
        for _ in range(len(self.api_keys)):
            key = self._select_viable_key()
            if not key or key in tried:
                break
            tried.add(key)
            try:
                async with aiohttp.ClientSession() as session:
                    # Essayer séquentiellement les modèles préférés puis le modèle par défaut
                    models_to_try = list(dict.fromkeys(self.preferred_models + [self.model]))
                    last_parse_error: Optional[str] = None
                    for model_slug in models_to_try:
                        try:
                            async with session.post(
                                f"{self.base_url}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {key}",
                                    "Content-Type": "application/json",
                                    "HTTP-Referer": self.http_referer,
                                    "X-Title": self.x_title,
                                },
                                json={
                                    "model": model_slug,
                                    "messages": [
                                        {
                                            "role": "user",
                                            "content": prompt
                                        }
                                    ],
                                    "max_tokens": 2000,
                                    "temperature": 0.1,
                                    "top_p": 0.9,
                                    "route": "fallback",
                                    "usage": {"include": True}
                                },
                                timeout=aiohttp.ClientTimeout(total=45)
                            ) as response:
                                if response.status != 200:
                                    text = await response.text()
                                    # Marquer la clé en échec si 429/5xx
                                    self._mark_key_failure(key, response.status in (429, 500, 502, 503, 504))
                                    logger.warning("OpenRouter model attempt failed", status=response.status, model=model_slug, text=text[:200])
                                    continue
                                
                                result = await response.json()
                                if "choices" not in result or len(result["choices"]) == 0:
                                    logger.warning("No choices in OpenRouter response", model=model_slug)
                                    continue
                                
                                content_text = result["choices"][0]["message"]["content"].strip()
                                content_text = self._clean_json_response(content_text)
                                try:
                                    structured_data = json.loads(content_text)
                                    # reset cooldown sur succès
                                    self._key_failures[key] = 0
                                    self._key_cooldown_until[key] = 0.0
                                    logger.info("OpenRouter request successful", response_length=len(content_text), model=model_slug, usage=result.get("usage"))
                                    return structured_data
                                except json.JSONDecodeError as e:
                                    last_parse_error = str(e)
                                    logger.warning("JSON parsing failed for model", model=model_slug, error=str(e), raw_content=content_text[:200])
                                    continue
                        except asyncio.TimeoutError as te:
                            last_error = te
                            self._mark_key_failure(key, True)
                            self._rotate_key()
                            break
                        except Exception as inner_e:
                            last_error = inner_e
                            is_rate = "429" in str(inner_e) or "rate" in str(inner_e).lower() or "quota" in str(inner_e).lower()
                            self._mark_key_failure(key, is_rate)
                            logger.warning("OpenRouter inner error on model", model=model_slug, error=str(inner_e))
                            continue
                    # Si on sort de la boucle sans retour, lever une erreur avec le dernier parsing error si disponible
                    if last_parse_error:
                        raise Exception(f"OpenRouter JSON parsing failed for all models: {last_parse_error}")
                    raise Exception("OpenRouter returned no valid choices for all models tried")
            except asyncio.TimeoutError as e:
                last_error = e
                self._mark_key_failure(key, True)
                self._rotate_key()
            except Exception as e:
                last_error = e
                # détecter rate-limit via message
                is_rate = "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower()
                self._mark_key_failure(key, is_rate)
                self._rotate_key()
        
        if last_error:
            raise Exception(f"OpenRouter request failed after rotating keys: {str(last_error)}")
        raise Exception("OpenRouter request failed: no viable key available")
    
    def _clean_json_response(self, content: str) -> str:
        """Nettoie la réponse pour extraire le JSON."""
        
        # Supprimer les balises markdown
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        # Supprimer les espaces et retours à la ligne en début/fin
        content = content.strip()
        
        # Si le contenu ne commence pas par {, essayer de trouver le JSON
        if not content.startswith("{"):
            start_idx = content.find("{")
            if start_idx != -1:
                content = content[start_idx:]
        
        # Si le contenu ne finit pas par }, essayer de trouver la fin du JSON
        if not content.endswith("}"):
            end_idx = content.rfind("}")
            if end_idx != -1:
                content = content[:end_idx + 1]
        
        return content
    
    def _create_fallback_response(self, raw_content: str, error: str) -> Dict[str, Any]:
        """Crée une réponse de fallback en cas d'échec du parsing JSON."""
        
        return {
            "title": "Extraction partielle",
            "company": "Non extrait",
            "location": "Non extrait",
            "job_type": "Non spécifié",
            "salary_range": None,
            "description": raw_content[:500] + "..." if len(raw_content) > 500 else raw_content,
            "requirements": "Non extraites",
            "benefits": None,
            "application_deadline": None,
            "experience_level": "Non spécifié",
            "education_level": "Non spécifié",
            "skills": [],
            "languages": [],
            "remote_work": None,
            "contact_info": None,
            "_parsing_error": error,
            "_raw_response": raw_content[:200] + "..." if len(raw_content) > 200 else raw_content
        }
    
    async def test_connection(self) -> bool:
        """Teste la connexion à l'API OpenRouter."""
        try:
            test_prompt = "Répondez avec ce JSON exact: {\"test\": \"success\", \"status\": \"ok\"}"
            result = await self._make_openrouter_request(test_prompt)
            return result.get("test") == "success"
        except Exception as e:
            logger.error("OpenRouter connection test failed", error=str(e))
            return False
    
    async def _enforce_rate_limit(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            dt = now - self._last_ts
            if dt < self._rate_delay:
                await asyncio.sleep(self._rate_delay - dt)
            self._last_ts = asyncio.get_event_loop().time()
    
    def _current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self._key_index % len(self.api_keys)]
    
    def _rotate_key(self):
        if not self.api_keys:
            return
        self._key_index = (self._key_index + 1) % len(self.api_keys)
    
    def _select_viable_key(self) -> Optional[str]:
        now = asyncio.get_event_loop().time()
        for i in range(len(self.api_keys)):
            idx = (self._key_index + i) % len(self.api_keys)
            key = self.api_keys[idx]
            if now >= self._key_cooldown_until.get(key, 0.0):
                self._key_index = idx
                return key
        return None
    
    def _mark_key_failure(self, key: Optional[str], backoffable: bool):
        if not key:
            return
        self._key_failures[key] = self._key_failures.get(key, 0) + 1
        if backoffable:
            cooldown = min(self._cooldown_base_seconds * (2 ** (self._key_failures[key] - 1)), self._max_cooldown_seconds)
            self._key_cooldown_until[key] = asyncio.get_event_loop().time() + cooldown
            logger.info("Applying cooldown to OpenRouter key", cooldown_seconds=cooldown, failures=self._key_failures[key])