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
    Utilise le modèle DeepSeek R1 gratuit pour la structuration des données.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek/deepseek-r1:free"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable.")
        
        logger.info("OpenRouterService initialized", model=self.model)
    
    async def structure_job_data(self, content: str, source_url: str, source_site: str) -> Dict[str, Any]:
        """
        Structure les données d'emploi extraites en utilisant OpenRouter.
        
        Args:
            content: Contenu brut extrait de la page d'emploi
            source_url: URL source de l'offre d'emploi
            source_site: Nom du site source (ex: 'emploi_tg')
            
        Returns:
            Dict contenant les données structurées
        """
        logger.info("Structuring job data with OpenRouter", 
                   content_length=len(content), url=source_url)
        
        try:
            # Construire le prompt de structuration
            prompt = self._build_structuring_prompt(content, source_url, source_site)
            
            # Faire l'appel à l'API OpenRouter
            result = await self._make_openrouter_request(prompt)
            
            # Ajouter les métadonnées d'extraction
            result["extraction_metadata"] = {
                "method": "openrouter",
                "provider_used": "deepseek",
                "source_site": source_site,
                "extracted_at": asyncio.get_event_loop().time(),
                "confidence_score": None,
                "enriched_fields": list(result.keys()),
                "processing_time_ms": None  # Sera calculé par l'appelant
            }
            
            logger.info("Job data structured successfully with OpenRouter",
                       url=source_url, fields_extracted=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Failed to structure job data with OpenRouter",
                        error=str(e), url=source_url)
            raise
    
    def _build_structuring_prompt(self, content: str, source_url: str, source_site: str) -> str:
        """Construit le prompt de structuration optimisé pour emploi.tg."""
        
        # Utiliser le prompt spécialisé emploi.tg si c'est la source
        if source_site == "emploi_tg":
            return self._build_emploitg_prompt(content, source_url)
        else:
            return self._build_generic_prompt(content, source_url, source_site)
    
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
        """Fait l'appel à l'API OpenRouter."""
        
        logger.info("Making OpenRouter request", prompt_length=len(prompt))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://jinascraper.local",
                        "X-Title": "JinaScraper",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.1,
                        "top_p": 0.9
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "choices" not in result or len(result["choices"]) == 0:
                        raise Exception("No choices in OpenRouter response")
                    
                    content_text = result["choices"][0]["message"]["content"].strip()
                    
                    # Nettoyer le contenu pour extraire le JSON
                    content_text = self._clean_json_response(content_text)
                    
                    # Parser le JSON
                    try:
                        structured_data = json.loads(content_text)
                        logger.info("OpenRouter request successful", 
                                   response_length=len(content_text))
                        return structured_data
                        
                    except json.JSONDecodeError as e:
                        logger.warning("JSON parsing failed, creating fallback response",
                                     error=str(e), raw_content=content_text[:200])
                        
                        # Créer une réponse de fallback
                        return self._create_fallback_response(content_text, str(e))
        
        except asyncio.TimeoutError:
            raise Exception("OpenRouter request timed out")
        except Exception as e:
            raise Exception(f"OpenRouter request failed: {str(e)}")
    
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