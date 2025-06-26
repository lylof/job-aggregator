from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ItemCacheBase(BaseModel):
    # =============== CHAMPS EXISTANTS (Compatibilité) ===============
    item_id: str
    item_provider: str
    item_type: str = 'job'  # 'job', 'bourse', etc.
    source_type: str  # 'api', 'rss', 'direct'
    source_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    item_posted_at: Optional[datetime] = None
    item_expires_at: Optional[datetime] = None
    item_title: Optional[str] = None
    company_name: Optional[str] = None
    item_employment_type: Optional[str] = None
    item_is_remote: Optional[bool] = False
    item_city: Optional[str] = None
    item_state: Optional[str] = None
    item_country: Optional[str] = None
    item_latitude: Optional[float] = None
    item_longitude: Optional[float] = None
    item_description: Optional[str] = None
    item_highlights: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any]
    sync_batch_id: Optional[str] = None
    is_active: Optional[bool] = True
    job_detailed: Optional[bool] = None
    details_fetched_at: Optional[datetime] = None
    job_full_data: Optional[Dict[str, Any]] = None

    # =============== NOUVEAUX CHAMPS ENRICHIS (Données LLM) ===============
    # Informations entreprise enrichies
    company_logo_url: Optional[str] = None
    company_website: Optional[str] = None  
    company_description: Optional[str] = None
    
    # Compétences et qualifications
    skills: Optional[List[str]] = None
    education_level: Optional[str] = None
    experience_level: Optional[str] = None
    languages: Optional[List[str]] = None
    
    # Informations contractuelles
    salary: Optional[str] = None
    number_of_positions: Optional[int] = None
    contract_type: Optional[str] = None  # Alias de item_employment_type pour cohérence
    
    # Classification métier
    sector: Optional[str] = None
    job_type: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Contact et candidature
    application_url: Optional[str] = None
    contact_email: Optional[str] = None
    other_benefits: Optional[str] = None
    
    # Profil recherché (texte enrichi)
    profile_required: Optional[str] = None

class ItemCacheResponse(ItemCacheBase):
    """Modèle de réponse API avec tous les champs enrichis disponibles"""
    pass 