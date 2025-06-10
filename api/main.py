from fastapi import FastAPI, Request, Response, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncpg
import time
import sys
import os
import platform
from typing import Callable

# Ajouter le répertoire racine au path pour les importations absolues
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root_dir)

# Utiliser des importations absolues qui fonctionnent toujours
from api.config import (
    API_TITLE, 
    API_DESCRIPTION, 
    API_VERSION, 
    API_PREFIX, 
    CORS_ORIGINS
)
from api.services.database import getDbPool, closeDbPool, DATABASE_URL
from api.routers import job_offers, search, statistics

# Création de l'application FastAPI
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json"
)

# Configuration du middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middleware pour le calcul du temps de réponse
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Gestion des erreurs
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(asyncpg.exceptions.PostgresError)
async def postgres_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur de base de données", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur serveur interne", "detail": str(exc)}
    )

# Événements de démarrage et d'arrêt
@app.on_event("startup")
async def startup_db_client():
    # Afficher des informations système pour le débogage
    print(f"Système d'exploitation: {platform.system()} {platform.release()}")
    print(f"Répertoire de travail: {os.getcwd()}")
    
    # Afficher la configuration de la base de données
    print(f"Tentative de connexion à la base de données PostgreSQL: {DATABASE_URL}")
    
    try:
        await getDbPool()
        print("Connexion à la base de données PostgreSQL établie avec succès")
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {e}")
        print("L'API fonctionnera en mode limité sans accès à la base de données")
        await app.state.db_available.set(False)

@app.on_event("shutdown")
async def shutdown():
    # Fermer le pool de connexions
    await closeDbPool()

# Route de base
@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API Job Aggregator. Consultez la documentation à /api/v1/docs"}

# Inclure les routeurs
app.include_router(job_offers.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(statistics.router, prefix=API_PREFIX)

# Point d'entrée pour le démarrage direct
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
