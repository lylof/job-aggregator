from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

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
