from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import sys
import os

# Ajouter le répertoire racine au path pour les importations absolues
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Utiliser des importations absolues
from api.models.responses import StatisticsResponse, ErrorResponse
from api.services.database import getJobStatistics
from api.dependencies import db_connection_required

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    responses={
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)

@router.get(
    "/", 
    response_model=StatisticsResponse,
    summary="Obtenir des statistiques sur les offres d'emploi",
    dependencies=[Depends(db_connection_required)]
)
async def get_statistics():
    """
    Récupère des statistiques agrégées sur toutes les offres d'emploi.
    
    Cette route fournit des informations comme :
    - Le nombre total d'offres
    - La répartition des offres par source
    - La répartition des offres par type de contrat
    - La répartition des offres par localisation (top 10)
    - La répartition des offres par niveau d'expérience
    - La répartition des offres par niveau d'éducation
    - Les compétences les plus demandées (top 20)
    
    Ces données sont utiles pour les tableaux de bord et les visualisations.
    """
    # Récupérer les statistiques
    statistics = await getJobStatistics()
    
    return statistics
