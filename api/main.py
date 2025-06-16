from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
import platform
from typing import Callable

# Ajouter le répertoire racine au path pour les importations absolues
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root_dir)

from api.config import (
    API_TITLE, 
    API_DESCRIPTION, 
    API_VERSION, 
    API_PREFIX, 
    CORS_ORIGINS
)
from api.routers import items

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur serveur interne", "detail": str(exc)}
    )

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API Job Aggregator 100% Supabase. Consultez la documentation à /api/v1/docs"}

app.include_router(items.router, prefix=API_PREFIX)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
