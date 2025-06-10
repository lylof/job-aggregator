import asyncpg
from asyncpg.pool import Pool
from typing import Optional, List, Dict, Any
import os
import sys

# Ajouter le répertoire parent au chemin pour permettre l'importation
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Définir directement la chaîne de connexion pour éviter les problèmes de chargement de configuration
DATABASE_URL = "postgresql://job_agg_user:1606@localhost:5432/job_aggregator_db"

# Afficher les informations de connexion pour vérification
print(f"Utilisation de la chaîne de connexion: {DATABASE_URL}")

# Note: Nous ne chargeons plus DATABASE_URL depuis config.py car il y a un problème avec le chargement
# try:
#     # Si exécuté comme module
#     from api.config import DATABASE_URL
# except ImportError:
#     # Si exécuté directement comme script
#     import sys
#     import os
#     sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     from config import DATABASE_URL

# Pool de connexions global
pool: Optional[Pool] = None

async def getDbPool() -> Optional[Pool]:
    """Récupère le pool de connexions à la base de données ou le crée s'il n'existe pas."""
    global pool
    if pool is None:
        try:
            print(f"Tentative de connexion à la base de données PostgreSQL: {DATABASE_URL}")
            pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20
            )
            print("Connexion à la base de données PostgreSQL établie avec succès")
        except Exception as e:
            print(f"Erreur de connexion à la base de données: {str(e)}")
            print("L'API fonctionnera en mode limité sans accès à la base de données")
            pool = None
    return pool

async def closeDbPool():
    """Ferme le pool de connexions à la base de données."""
    global pool
    if pool:
        await pool.close()
        pool = None

async def getJobOffers(
    page: int = 1, 
    pageSize: int = 20, 
    filters: Dict[str, Any] = None, 
    orderBy: str = "scrape_timestamp", 
    orderDir: str = "desc"
) -> List[Dict[str, Any]]:
    """
    Récupère les offres d'emploi en fonction des filtres et de la pagination.
    
    Args:
        page: Numéro de page (commence à 1)
        pageSize: Nombre d'éléments par page
        filters: Dictionnaire de filtres à appliquer
        orderBy: Champ de tri
        orderDir: Direction du tri ('asc' ou 'desc')
        
    Returns:
        Liste des offres d'emploi
    """
    pool = await getDbPool()
    
    # Calcul de l'offset pour la pagination
    offset = (page - 1) * pageSize
    
    # Construction de la requête de base
    query = "SELECT * FROM job_offers"
    queryParams = []
    paramIndex = 1
    
    # Ajout des filtres si présents
    if filters:
        whereConditions = []
        
        # Traitement des filtres textuels avec recherche partielle
        for field, value in filters.items():
            if field in ["title", "company", "location", "description", "summary"]:
                whereConditions.append(f"{field} ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "required_skills" and isinstance(value, list):
                # Recherche des compétences dans le tableau required_skills
                skillsConditions = []
                for skill in value:
                    skillsConditions.append(f"${paramIndex} = ANY(required_skills)")
                    queryParams.append(skill)
                    paramIndex += 1
                if skillsConditions:
                    whereConditions.append(f"({' OR '.join(skillsConditions)})")
            elif field == "salary":
                # Filtre sur le salaire (recherche textuelle)
                whereConditions.append(f"salary ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "contract_type_normalized":
                # Filtre exact sur le type de contrat normalisé
                whereConditions.append(f"contract_type_normalized = ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
            elif field == "education_level":
                # Filtre sur le niveau d'éducation
                whereConditions.append(f"education_level ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "required_experience":
                # Filtre sur l'expérience requise
                whereConditions.append(f"required_experience ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "publish_date_from":
                # Filtre sur la date de publication (date minimum)
                whereConditions.append(f"publish_date_parsed >= ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
            elif field == "publish_date_to":
                # Filtre sur la date de publication (date maximum)
                whereConditions.append(f"publish_date_parsed <= ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
        
        # Ajout des conditions WHERE si présentes
        if whereConditions:
            query += f" WHERE {' AND '.join(whereConditions)}"
    
    # Ajout du tri
    if orderBy in ["title", "company", "location", "publish_date_parsed", "scrape_timestamp"]:
        direction = "ASC" if orderDir.lower() == "asc" else "DESC"
        query += f" ORDER BY {orderBy} {direction}"
    else:
        # Tri par défaut si le champ spécifié n'est pas valide
        query += " ORDER BY scrape_timestamp DESC"
    
    # Ajout de la pagination
    query += f" LIMIT ${paramIndex} OFFSET ${paramIndex + 1}"
    queryParams.extend([pageSize, offset])
    
    # Exécution de la requête
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *queryParams)
        
    # Conversion en dictionnaires
    results = []
    for row in rows:
        # Convertir les types de données PostgreSQL en types Python
        offer = dict(row)
        results.append(offer)
    
    return results

async def getJobOfferById(jobId: int) -> Optional[Dict[str, Any]]:
    """
    Récupère une offre d'emploi par son ID.
    
    Args:
        jobId: ID de l'offre d'emploi
        
    Returns:
        Détails de l'offre d'emploi ou None si non trouvée
    """
    pool = await getDbPool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM job_offers WHERE id = $1", jobId)
        
    if row:
        return dict(row)
    
    return None

async def countJobOffers(filters: Dict[str, Any] = None) -> int:
    """
    Compte le nombre total d'offres d'emploi correspondant aux filtres.
    
    Args:
        filters: Dictionnaire de filtres à appliquer
        
    Returns:
        Nombre total d'offres d'emploi
    """
    pool = await getDbPool()
    
    # Construction de la requête de base
    query = "SELECT COUNT(*) FROM job_offers"
    queryParams = []
    paramIndex = 1
    
    # Ajout des filtres si présents
    if filters:
        whereConditions = []
        
        # Traitement des filtres textuels avec recherche partielle
        for field, value in filters.items():
            if field in ["title", "company", "location", "description", "summary"]:
                whereConditions.append(f"{field} ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "required_skills" and isinstance(value, list):
                # Recherche des compétences dans le tableau required_skills
                skillsConditions = []
                for skill in value:
                    skillsConditions.append(f"${paramIndex} = ANY(required_skills)")
                    queryParams.append(skill)
                    paramIndex += 1
                if skillsConditions:
                    whereConditions.append(f"({' OR '.join(skillsConditions)})")
            elif field == "salary":
                # Filtre sur le salaire (recherche textuelle)
                whereConditions.append(f"salary ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "contract_type_normalized":
                # Filtre exact sur le type de contrat normalisé
                whereConditions.append(f"contract_type_normalized = ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
            elif field == "education_level":
                # Filtre sur le niveau d'éducation
                whereConditions.append(f"education_level ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "required_experience":
                # Filtre sur l'expérience requise
                whereConditions.append(f"required_experience ILIKE ${paramIndex}")
                queryParams.append(f"%{value}%")
                paramIndex += 1
            elif field == "publish_date_from":
                # Filtre sur la date de publication (date minimum)
                whereConditions.append(f"publish_date_parsed >= ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
            elif field == "publish_date_to":
                # Filtre sur la date de publication (date maximum)
                whereConditions.append(f"publish_date_parsed <= ${paramIndex}")
                queryParams.append(value)
                paramIndex += 1
        
        # Ajout des conditions WHERE si présentes
        if whereConditions:
            query += f" WHERE {' AND '.join(whereConditions)}"
    
    # Exécution de la requête
    async with pool.acquire() as conn:
        count = await conn.fetchval(query, *queryParams)
        
    return count

async def getJobStatistics() -> Dict[str, Any]:
    """
    Récupère les statistiques générales sur les offres d'emploi.
    
    Returns:
        Statistiques sur les offres d'emploi
    """
    pool = await getDbPool()
    
    async with pool.acquire() as conn:
        # Nombre total d'offres
        totalJobs = await conn.fetchval("SELECT COUNT(*) FROM job_offers")
        
        # Nombre d'offres par source
        jobsBySource = await conn.fetch("SELECT source, COUNT(*) as count FROM job_offers GROUP BY source ORDER BY count DESC")
        
        # Nombre d'offres par type de contrat
        jobsByContractType = await conn.fetch("""
            SELECT 
                COALESCE(contract_type_normalized, 'Non spécifié') as contract_type, 
                COUNT(*) as count 
            FROM job_offers 
            GROUP BY contract_type_normalized 
            ORDER BY count DESC
        """)
        
        # Nombre d'offres par localisation (top 10)
        jobsByLocation = await conn.fetch("""
            SELECT 
                COALESCE(location, 'Non spécifié') as location, 
                COUNT(*) as count 
            FROM job_offers 
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        # Nombre d'offres par niveau d'expérience
        jobsByExperience = await conn.fetch("""
            SELECT 
                COALESCE(required_experience, 'Non spécifié') as experience, 
                COUNT(*) as count 
            FROM job_offers 
            GROUP BY required_experience 
            ORDER BY count DESC
        """)
        
        # Nombre d'offres par niveau d'éducation
        jobsByEducation = await conn.fetch("""
            SELECT 
                COALESCE(education_level, 'Non spécifié') as education, 
                COUNT(*) as count 
            FROM job_offers 
            GROUP BY education_level 
            ORDER BY count DESC
        """)
        
        # Top compétences demandées
        topSkills = await conn.fetch("""
            SELECT skill, COUNT(*) as count
            FROM (
                SELECT unnest(required_skills) as skill 
                FROM job_offers 
                WHERE required_skills IS NOT NULL
            ) as skills
            GROUP BY skill
            ORDER BY count DESC
            LIMIT 20
        """)
    
    # Formatage des résultats
    return {
        "total_jobs": totalJobs,
        "jobs_by_source": [dict(row) for row in jobsBySource],
        "jobs_by_contract_type": [dict(row) for row in jobsByContractType],
        "jobs_by_location": [dict(row) for row in jobsByLocation],
        "jobs_by_experience": [dict(row) for row in jobsByExperience],
        "jobs_by_education": [dict(row) for row in jobsByEducation],
        "top_skills": [dict(row) for row in topSkills]
    }

async def searchJobOffers(
    query: str,
    page: int = 1,
    pageSize: int = 20,
    orderBy: str = "relevance"
) -> List[Dict[str, Any]]:
    """
    Recherche des offres d'emploi en fonction d'une requête textuelle.
    
    Args:
        query: Texte de recherche
        page: Numéro de page (commence à 1)
        pageSize: Nombre d'éléments par page
        orderBy: Champ de tri ('relevance', 'date', etc.)
        
    Returns:
        Liste des offres d'emploi correspondant à la recherche
    """
    pool = await getDbPool()
    
    # Calcul de l'offset pour la pagination
    offset = (page - 1) * pageSize
    
    # Construction de la requête de recherche
    # Utilisation de to_tsvector et to_tsquery pour la recherche plein texte
    searchQuery = """
    SELECT 
        *,
        ts_rank_cd(
            setweight(to_tsvector('french', COALESCE(title, '')), 'A') ||
            setweight(to_tsvector('french', COALESCE(company, '')), 'B') ||
            setweight(to_tsvector('french', COALESCE(summary, '')), 'C') ||
            setweight(to_tsvector('french', COALESCE(description, '')), 'D'),
            plainto_tsquery('french', $1)
        ) as relevance
    FROM job_offers
    WHERE 
        to_tsvector('french', COALESCE(title, '') || ' ' || 
                             COALESCE(company, '') || ' ' || 
                             COALESCE(summary, '') || ' ' || 
                             COALESCE(description, '')) @@ plainto_tsquery('french', $1)
        OR EXISTS (
            SELECT 1 FROM unnest(required_skills) skill
            WHERE skill ILIKE '%' || $1 || '%'
        )
    """
    
    # Ajout du tri
    if orderBy == "date":
        searchQuery += " ORDER BY publish_date_parsed DESC NULLS LAST"
    elif orderBy == "company":
        searchQuery += " ORDER BY company ASC NULLS LAST"
    else:  # Par défaut, tri par pertinence
        searchQuery += " ORDER BY relevance DESC"
    
    # Ajout de la pagination
    searchQuery += " LIMIT $2 OFFSET $3"
    
    # Exécution de la requête
    async with pool.acquire() as conn:
        rows = await conn.fetch(searchQuery, query, pageSize, offset)
    
    # Conversion en dictionnaires
    results = []
    for row in rows:
        offer = dict(row)
        # Supprimer le score de pertinence du résultat final (utilisé uniquement pour le tri)
        if "relevance" in offer:
            del offer["relevance"]
        results.append(offer)
    
    return results

async def countSearchResults(query: str) -> int:
    """
    Compte le nombre total de résultats pour une recherche.
    
    Args:
        query: Texte de recherche
        
    Returns:
        Nombre total de résultats
    """
    pool = await getDbPool()
    
    # Construction de la requête de comptage
    countQuery = """
    SELECT COUNT(*)
    FROM job_offers
    WHERE 
        to_tsvector('french', COALESCE(title, '') || ' ' || 
                             COALESCE(company, '') || ' ' || 
                             COALESCE(summary, '') || ' ' || 
                             COALESCE(description, '')) @@ plainto_tsquery('french', $1)
        OR EXISTS (
            SELECT 1 FROM unnest(required_skills) skill
            WHERE skill ILIKE '%' || $1 || '%'
        )
    """
    
    # Exécution de la requête
    async with pool.acquire() as conn:
        count = await conn.fetchval(countQuery, query)
    
    return count
