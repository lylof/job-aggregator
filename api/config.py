import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_USER = os.getenv("DB_USER", "job_agg_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1606")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "job_aggregator")

# Afficher les informations de connexion pour le débogage
print(f"Informations de connexion chargées - Utilisateur: {DB_USER}, Base: {DB_NAME}")

# Construction de la chaîne de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuration de l'API
API_VERSION = "v1"
API_TITLE = "Job Aggregator API"
API_DESCRIPTION = "API pour accéder aux offres d'emploi enrichies du Job Aggregator"
API_PREFIX = f"/api/{API_VERSION}"

# Paramètres de pagination par défaut
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cors settings
CORS_ORIGINS = [
    "http://localhost:3000",  # React frontend
    "http://localhost:8000",  # Developpement local
    "*"  # Toutes les origines (pour le développement uniquement)
]
