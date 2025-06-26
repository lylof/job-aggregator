import os
import logging
from typing import Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
from dateutil import parser as dateparser


def _normalize_date(value: Any):
    """Convert various date string formats to ISO YYYY-MM-DD accepted by Postgres.
    Leaves the value unchanged if parsing fails or if it's not a string.
    """
    if isinstance(value, str):
        cleaned = value.strip()
        # Remove common French prefixes indicating publication wording
        for prefix in ["Publiée le", "Publié le"]:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        try:
            dt = dateparser.parse(cleaned, dayfirst=True)
            if dt is not None:
                return dt.date().isoformat()
        except Exception:
            pass
    return value


# Chargement des variables d'environnement
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis dans le .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Champs standards de la table items_cache
# Champs standards étendus de la table items_cache (ajout de champs demandés)
ITEMS_CACHE_FIELDS = {
    'item_id', 'item_provider', 'item_type', 'source_type', 'source_name', 'created_at', 'updated_at',
    'item_posted_at', 'item_expires_at', 'item_title', 'company_name', 'item_employment_type',
    'item_is_remote', 'item_city', 'item_state', 'item_country', 'item_latitude', 'item_longitude',
    'item_description', 'item_highlights', 'raw_data', 'sync_batch_id', 'is_active',
    'job_detailed', 'details_fetched_at', 'job_full_data',
    # champs enrichis LLM
    'company_logo_url', 'company_website', 'company_description',
    'skills', 'salary', 'languages', 'sector', 'education_level', 'experience_level',
    'number_of_positions', 'tags', 'contact_email', 'other_benefits', 'application_url',
    # classification automatique et géolocalisation Phase 2
    'offer_category', 'detected_city', 'detected_region', 'detected_latitude', 'detected_longitude', 'remote_work_detected'
}

def map_job_offer_to_items_cache(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mappe un job du crawler (JobOffer) vers le schéma items_cache.
    Les champs non standards sont stockés dans raw_data.
    """
    mapped = {}
    raw_data = {}
    # Mapping explicite de certains champs du modèle JobOffer vers les colonnes standard
    FIELD_MAP = {
        # Principaux champs existants
        "title": "item_title",
        "company_name": "company_name",
        "job_description": "item_description",
        "location": "item_city",
        "remote_possible": "item_is_remote",
        "date_posted": "item_posted_at",
        "valid_through": "item_expires_at",
        "contract_type": "item_employment_type",
        "job_type": "item_employment_type",
        # Champs enrichis LLM
        "company_logo_url": "company_logo_url",
        "company_website": "company_website",
        "company_description": "company_description",
        "skills": "skills",
        "salary": "salary",
        "languages": "languages",
        "sector": "sector",
        "education_level": "education_level",
        "experience_level": "experience_level",
        "number_of_positions": "number_of_positions",
        "tags": "tags",
        "contact_email": "contact_email",
        "other_benefits": "other_benefits",
        "application_url": "application_url",
        # Classification automatique et géolocalisation Phase 2
        "offer_category": "offer_category",
        "detected_city": "detected_city",
        "detected_region": "detected_region", 
        "detected_latitude": "detected_latitude",
        "detected_longitude": "detected_longitude",
        "remote_work_detected": "remote_work_detected"
    }

    for k, v in job.items():
        target = FIELD_MAP.get(k, k)
        if target in ITEMS_CACHE_FIELDS:
            mapped[target] = v
        else:
            raw_data[k] = v
    mapped['raw_data'] = raw_data
    # Champs obligatoires minimum
    mapped.setdefault('item_id', job.get('item_id') or job.get('source_url') or job.get('url'))
    mapped.setdefault('item_provider', 'crawler')
    mapped.setdefault('item_type', 'job')
    mapped.setdefault('source_type', 'web')
    mapped.setdefault('is_active', True)
    # Normalize date fields to ISO format to avoid Postgres datestyle errors
    for date_field in ("item_posted_at", "item_expires_at"):
        if date_field in mapped:
            mapped[date_field] = _normalize_date(mapped[date_field])
    return mapped

def upsert_job_to_supabase(job: Dict[str, Any]) -> bool:
    """
    Upsert une offre dans la table items_cache.
    Retourne True si succès, False sinon.
    """
    try:
        mapped = map_job_offer_to_items_cache(job)
        response = supabase.table("items_cache").upsert(mapped).execute()
        # La lib Supabase renvoie un objet avec `.data` et `.error`.
        # On considère que l'upsert est réussi s'il n'y a pas d'erreur.
        if getattr(response, "error", None) is None:
            logging.info(f"[SUPABASE] Upsert OK: {mapped.get('item_id')}")
            return True
        else:
            logging.error(f"[SUPABASE] Upsert FAIL: {mapped.get('item_id')} | Error: {response.error}")
            return False
    except Exception as e:
        logging.error(f"[SUPABASE] Exception upsert {job.get('item_id')}: {e}")
        return False