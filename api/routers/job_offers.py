from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

# Ajouter le répertoire racine au path pour les importations absolues
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Utiliser des importations absolues
from api.models.job_offer import JobOfferResponse, JobOfferCreate, JobOfferUpdate
from api.models.responses import PaginatedResponse, ErrorResponse, SuccessResponse
from api.services.database import getJobOffers, getJobOfferById, countJobOffers
from api.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from api.dependencies import db_connection_required

router = APIRouter(
    prefix="/job-offers",
    tags=["job-offers"],
    responses={
        404: {"model": ErrorResponse, "description": "Offre d'emploi non trouvée"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)

@router.get(
    "/", 
    response_model=PaginatedResponse[JobOfferResponse],
    summary="Récupérer toutes les offres d'emploi avec pagination et filtres",
    dependencies=[Depends(db_connection_required)]
)
async def get_job_offers(
    page: int = Query(1, ge=1, description="Numéro de page (commence à 1)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page"),
    title: Optional[str] = Query(None, description="Filtre sur le titre de l'offre"),
    company: Optional[str] = Query(None, description="Filtre sur l'entreprise"),
    location: Optional[str] = Query(None, description="Filtre sur la localisation"),
    contract_type: Optional[str] = Query(None, description="Filtre sur le type de contrat normalisé"),
    skill: Optional[List[str]] = Query(None, description="Filtre sur les compétences requises"),
    experience: Optional[str] = Query(None, description="Filtre sur l'expérience requise"),
    education: Optional[str] = Query(None, description="Filtre sur le niveau d'éducation"),
    publish_date_from: Optional[datetime] = Query(None, description="Date de publication minimum"),
    publish_date_to: Optional[datetime] = Query(None, description="Date de publication maximum"),
    order_by: str = Query("scrape_timestamp", description="Champ de tri"),
    order_dir: str = Query("desc", description="Direction du tri ('asc' ou 'desc')")
):
    """
    Récupère toutes les offres d'emploi avec pagination et filtres optionnels.
    
    Cette route permet de :
    - Filtrer les offres par titre, entreprise, localisation, etc.
    - Paginer les résultats
    - Trier les résultats par différents champs
    
    Exemples de filtrage :
    - `/job-offers?title=développeur` : Recherche les offres contenant "développeur" dans le titre
    - `/job-offers?company=google` : Recherche les offres de Google
    - `/job-offers?location=paris` : Recherche les offres à Paris
    - `/job-offers?contract_type=CDI` : Recherche les CDI
    - `/job-offers?skill=python&skill=react` : Recherche les offres demandant Python ET React
    """
    # Construire les filtres à partir des paramètres de requête
    filters = {}
    
    if title:
        filters["title"] = title
    if company:
        filters["company"] = company
    if location:
        filters["location"] = location
    if contract_type:
        filters["contract_type_normalized"] = contract_type
    if skill:
        filters["required_skills"] = skill
    if experience:
        filters["required_experience"] = experience
    if education:
        filters["education_level"] = education
    if publish_date_from:
        filters["publish_date_from"] = publish_date_from
    if publish_date_to:
        filters["publish_date_to"] = publish_date_to
    
    # Récupérer les offres d'emploi avec pagination et filtres
    job_offers = await getJobOffers(
        page=page,
        pageSize=page_size,
        filters=filters,
        orderBy=order_by,
        orderDir=order_dir
    )
    
    # Compter le nombre total d'offres correspondant aux filtres
    total = await countJobOffers(filters)
    
    # Créer et retourner la réponse paginée
    return PaginatedResponse.create(
        items=job_offers,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get(
    "/{job_id}", 
    response_model=JobOfferResponse,
    summary="Récupérer une offre d'emploi par son ID",
    dependencies=[Depends(db_connection_required)]
)
async def get_job_offer(
    job_id: int = Path(..., ge=1, description="ID de l'offre d'emploi")
):
    """
    Récupère les détails d'une offre d'emploi spécifique par son ID.
    
    Cette route retourne toutes les informations détaillées d'une offre d'emploi,
    y compris les champs enrichis comme le résumé, les compétences requises, etc.
    """
    job_offer = await getJobOfferById(job_id)
    
    if job_offer is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Offre d'emploi avec l'ID {job_id} non trouvée"
        )
    
    return job_offer

@router.get(
    "/slug/{slug}", 
    response_model=JobOfferResponse,
    summary="Récupérer une offre d'emploi par son slug",
    dependencies=[Depends(db_connection_required)]
)
async def get_job_offer_by_slug(
    slug: str = Path(..., description="Slug SEO de l'offre d'emploi")
):
    """
    Récupère les détails d'une offre d'emploi spécifique par son slug SEO.
    
    Cette route est utile pour les URLs SEO-friendly dans l'interface utilisateur.
    """
    # Construire le filtre pour la recherche par slug
    filters = {"slug": slug}
    
    # Rechercher l'offre avec le slug spécifié
    job_offers = await getJobOffers(page=1, pageSize=1, filters=filters)
    
    if not job_offers:
        raise HTTPException(
            status_code=404, 
            detail=f"Offre d'emploi avec le slug '{slug}' non trouvée"
        )
    
    return job_offers[0]
