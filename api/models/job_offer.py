from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobOfferBase(BaseModel):
    """Modèle de base pour les offres d'emploi."""
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    date_posted: Optional[str] = None
    contract_type: Optional[str] = None
    source: str
    source_page_url: Optional[str] = None
    apply_url: Optional[str] = None
    
    # Champs enrichis
    summary: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience: Optional[str] = None
    education_level: Optional[str] = None
    salary: Optional[str] = None
    company_logo: Optional[str] = None
    application_deadline: Optional[str] = None
    slug: Optional[str] = None
    keywords: Optional[List[str]] = None
    contract_type_normalized: Optional[str] = None

class JobOfferInDB(JobOfferBase):
    """Modèle pour les offres d'emploi stockées en base de données."""
    id: int
    url: str
    publish_date_parsed: Optional[datetime] = None
    is_new: bool = True
    scrape_timestamp: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        orm_mode = True

class JobOfferResponse(JobOfferInDB):
    """Modèle pour les réponses d'API contenant des offres d'emploi."""
    pass

class JobOfferCreate(JobOfferBase):
    """Modèle pour la création d'offres d'emploi."""
    url: str
    
class JobOfferUpdate(BaseModel):
    """Modèle pour la mise à jour d'offres d'emploi."""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    date_posted: Optional[str] = None
    contract_type: Optional[str] = None
    source: Optional[str] = None
    source_page_url: Optional[str] = None
    apply_url: Optional[str] = None
    summary: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_experience: Optional[str] = None
    education_level: Optional[str] = None
    salary: Optional[str] = None
    company_logo: Optional[str] = None
    application_deadline: Optional[str] = None
    slug: Optional[str] = None
    keywords: Optional[List[str]] = None
    contract_type_normalized: Optional[str] = None
