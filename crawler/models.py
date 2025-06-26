from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class JobOffer(BaseModel):
    title: str = Field(..., description="Titre du poste")
    company_name: str = Field(..., description="Nom de l'entreprise")
    company_logo_url: Optional[str] = Field(None, description="Logo de l'entreprise")
    company_website: Optional[str] = Field(None, description="Site web de l'entreprise")
    company_description: Optional[str] = Field(None, description="Description de l'entreprise")
    location: str = Field(..., description="Lieu (ville, région, pays)")
    remote_possible: Optional[bool] = Field(None, description="Télétravail possible")
    date_posted: Optional[str] = Field(None, description="Date de publication")
    valid_through: Optional[str] = Field(None, description="Date de fin de validité de l'offre")
    contract_type: Optional[str] = Field(None, description="Type de contrat (CDI, CDD, Stage, etc.)")
    job_description: str = Field(..., description="Description complète du poste")
    profile_required: Optional[str] = Field(None, description="Profil recherché (compétences, expérience, formation)")
    skills: Optional[List[str]] = Field(None, description="Compétences clés")
    education_level: Optional[str] = Field(None, description="Niveau d'études requis")
    experience_level: Optional[str] = Field(None, description="Niveau d'expérience requis")
    salary: Optional[str] = Field(None, description="Salaire")
    languages: Optional[List[str]] = Field(None, description="Langues exigées")
    number_of_positions: Optional[int] = Field(None, description="Nombre de postes à pourvoir")
    application_url: Optional[str] = Field(None, description="Lien pour postuler")
    source_url: str = Field(..., description="URL d'origine de l'offre")
    sector: Optional[str] = Field(None, description="Secteur d'activité")
    job_type: Optional[str] = Field(None, description="Métier / catégorie")
    tags: Optional[List[str]] = Field(None, description="Mots-clés additionnels")
    contact_email: Optional[str] = Field(None, description="Email de contact")
    other_benefits: Optional[str] = Field(None, description="Avantages divers")
    
    # ==================== NOUVEAUX CHAMPS PHASE 2 ====================
    offer_category: Optional[str] = Field(None, description="Catégorie automatique: job, internship, scholarship, training, volunteer")
    detected_city: Optional[str] = Field(None, description="Ville détectée automatiquement")
    detected_region: Optional[str] = Field(None, description="Région détectée automatiquement")
    detected_latitude: Optional[float] = Field(None, description="Latitude de la ville détectée")
    detected_longitude: Optional[float] = Field(None, description="Longitude de la ville détectée")
    remote_work_detected: Optional[bool] = Field(None, description="Télétravail détecté automatiquement")

    # -------------------- VALIDATORS --------------------
    @field_validator('skills', 'languages', 'tags', mode='before')
    @classmethod
    def _ensure_list(cls, v):
        """Permettre de passer une chaîne séparée par virgules ou une liste."""
        if v is None:
            return v
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # découpe sur virgule ou retour à la ligne
            parts = [p.strip() for p in v.replace('\n', ',').split(',')]
            return [p for p in parts if p]
        # toute autre valeur : laisser Pydantic gérer
        return v

    @field_validator('number_of_positions', mode='before')
    @classmethod
    def _coerce_int(cls, v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        # Essaye de convertir les chaînes numériques
        try:
            return int(v)
        except Exception:
            return v 