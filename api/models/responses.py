from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Modèle pour les réponses paginées de l'API."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """Crée une réponse paginée à partir des paramètres fournis."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur de l'API."""
    error: str
    detail: Optional[str] = None
    status_code: int = 400

class SuccessResponse(BaseModel):
    """Modèle pour les réponses de succès de l'API."""
    message: str
    data: Optional[Dict[str, Any]] = None

class StatisticsResponse(BaseModel):
    """Modèle pour les réponses de statistiques."""
    total_jobs: int
    jobs_by_source: List[Dict[str, Any]]
    jobs_by_contract_type: List[Dict[str, Any]]
    jobs_by_location: List[Dict[str, Any]]
    jobs_by_experience: List[Dict[str, Any]]
    jobs_by_education: List[Dict[str, Any]]
    top_skills: List[Dict[str, Any]]
