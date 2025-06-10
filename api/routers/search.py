from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from typing import List, Dict, Any, Optional
import sys
import os

# Ajouter le répertoire racine au path pour les importations absolues
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Utiliser des importations absolues
from api.models.job_offer import JobOfferResponse
from api.models.responses import PaginatedResponse, ErrorResponse
from api.services.database import searchJobOffers, countSearchResults
from api.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from api.dependencies import db_connection_required

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)

@router.get(
    "/", 
    response_model=PaginatedResponse[JobOfferResponse],
    summary="Rechercher des offres d'emploi",
    dependencies=[Depends(db_connection_required)]
)
async def search_job_offers(
    q: str = Query(..., min_length=2, description="Texte de recherche"),
    page: int = Query(1, ge=1, description="Numéro de page (commence à 1)"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page"),
    order_by: str = Query("relevance", description="Champ de tri ('relevance', 'date', 'company')")
):
    """
    Recherche des offres d'emploi en fonction d'une requête textuelle.
    
    Cette route utilise une recherche plein texte pour trouver les offres d'emploi
    correspondant à la requête dans le titre, l'entreprise, le résumé, la description
    ou les compétences requises.
    
    Exemples de recherche :
    - `/search?q=développeur` : Recherche les offres liées au développement
    - `/search?q=javascript paris` : Recherche les offres mentionnant JavaScript à Paris
    - `/search?q=senior backend` : Recherche les offres de développeur backend senior
    
    Le tri peut se faire par :
    - `relevance` : Pertinence par rapport à la requête (par défaut)
    - `date` : Date de publication (du plus récent au plus ancien)
    - `company` : Nom de l'entreprise (ordre alphabétique)
    """
    # Rechercher les offres d'emploi correspondant à la requête
    job_offers = await searchJobOffers(
        query=q,
        page=page,
        pageSize=page_size,
        orderBy=order_by
    )
    
    # Compter le nombre total de résultats
    total = await countSearchResults(q)
    
    # Créer et retourner la réponse paginée
    return PaginatedResponse.create(
        items=job_offers,
        total=total,
        page=page,
        page_size=page_size
    )
