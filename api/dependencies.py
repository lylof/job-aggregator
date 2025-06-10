from fastapi import HTTPException, Depends, status
from typing import Optional, Callable, Any
import asyncpg
from .services.database import getDbPool

async def db_connection_required():
    """
    Dépendance qui vérifie si la connexion à la base de données est disponible.
    À utiliser avec Depends() dans les endpoints qui nécessitent une connexion à la base de données.
    Lève une exception 503 Service Unavailable si la base de données n'est pas disponible.
    """
    db_pool = await getDbPool()
    if db_pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de données temporairement indisponible. Veuillez réessayer ultérieurement."
        )
    return db_pool
