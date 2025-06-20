import json
from typing import Dict, Any
from .models import JobOffer

# Prompt universel pour l'enrichissement, plus strict
ENRICHMENT_PROMPT = (
    "Voici une offre d'emploi extraite d'un site. Complète les champs manquants (skills, education_level, experience_level, languages, salary, etc.) en t'appuyant uniquement sur le texte de job_description et profile_required. "
    "Retourne uniquement le JSON, sans balise markdown, sans texte autour, et uniquement les champs du modèle suivant : "
    "title, company_name, company_logo_url, company_website, company_description, location, remote_possible, date_posted, valid_through, contract_type, job_description, profile_required, skills, education_level, experience_level, salary, languages, number_of_positions, application_url, source_url, sector, job_type, tags, contact_email, other_benefits. "
    "Ne réécris pas la description. Si l'info n'est pas présente, laisse le champ à null."
)

def build_enrichment_prompt(job_offer: Dict[str, Any]) -> str:
    return f"{ENRICHMENT_PROMPT}\n\n{json.dumps(job_offer, ensure_ascii=False, indent=2)}"

class LLMEnricher:
    """
    Interface générique pour l'enrichissement LLM.
    """
    def enrich(self, job_offer: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class GeminiEnricher(LLMEnricher):
    """
    Implémentation pour Google Gemini (API Google AI Studio).
    """
    def __init__(self, api_key: str):
        import google.generativeai as genai
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def enrich(self, job_offer: Dict[str, Any]) -> Dict[str, Any]:
        prompt = build_enrichment_prompt(job_offer)
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        # Gestion des blocs markdown (```json ... ```)
        if text.startswith('```json'):
            text = text[7:].strip()
            if text.endswith('```'):
                text = text[:-3].strip()
        elif text.startswith('```'):
            text = text[3:].strip()
            if text.endswith('```'):
                text = text[:-3].strip()
        # Parsing JSON principal
        try:
            enriched_json = json.loads(text, strict=False)
            print("[LLM enrich] JSON parsing OK")
        except Exception as e:
            print(f"[LLM enrich error] JSON parsing failed: {e}")
            print(f"[LLM raw response]:\n{text}\n")
            # Fallback regex pour extraire le JSON d'un texte
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    enriched_json = json.loads(match.group(0), strict=False)
                    print("[LLM enrich] Fallback JSON parsing OK")
                except Exception as e2:
                    print(f"[LLM enrich error] Fallback JSON parsing failed: {e2}")
                    return job_offer
            else:
                return job_offer
        # Filtrage strict des champs selon le modèle
        allowed_fields = set(JobOffer.model_fields.keys())
        enriched_json = {k: v for k, v in enriched_json.items() if k in allowed_fields}
        # Normalisation avancée
        enriched_json = self._normalize_enriched(enriched_json)
        # Audit des modifications
        self._log_enrichment_diff(job_offer, enriched_json)
        return {**job_offer, **enriched_json}

    def _normalize_enriched(self, enriched: dict) -> dict:
        # Normalise remote_possible en booléen
        if 'remote_possible' in enriched:
            val = enriched['remote_possible']
            if isinstance(val, str):
                enriched['remote_possible'] = val.strip().lower() in ("oui", "yes", "true", "1")
        # Nettoie les tags (liste de str, pas de doublons)
        if 'tags' in enriched and isinstance(enriched['tags'], list):
            enriched['tags'] = list({t.strip() for t in enriched['tags'] if t and isinstance(t, str)})
        # Normalise education_level
        EDUCATION_MAP = {
            "bac+3": "Bac+3",
            "bac+4": "Bac+4",
            "bac+5": "Bac+5",
            "baccalauréat": "Bac",
            "aucun certificat, diplôme ou grade": "Aucun diplôme"
        }
        if 'education_level' in enriched and enriched['education_level']:
            v = enriched['education_level'].strip().lower()
            enriched['education_level'] = EDUCATION_MAP.get(v, enriched['education_level'])
        # Normalise experience_level
        EXP_MAP = {
            "junior": "Junior",
            "mid-senior level": "Confirmé",
            "senior": "Senior",
            "débutant": "Débutant"
        }
        if 'experience_level' in enriched and enriched['experience_level']:
            v = enriched['experience_level'].strip().lower()
            enriched['experience_level'] = EXP_MAP.get(v, enriched['experience_level'])
        # number_of_positions en int
        if 'number_of_positions' in enriched and enriched['number_of_positions'] is not None:
            try:
                enriched['number_of_positions'] = int(enriched['number_of_positions'])
            except Exception:
                enriched['number_of_positions'] = None
        return enriched

    def _log_enrichment_diff(self, before: dict, after: dict):
        diff = {k: (before.get(k), after[k]) for k in after if before.get(k) != after[k]}
        if diff:
            print(f"[LLM enrich] Champs modifiés : {diff}")
        else:
            print("[LLM enrich] Aucun champ modifié par l'IA.")

# Extension possible :
# class OpenRouterEnricher(LLMEnricher): ... 