from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional
from api.models.items_cache import ItemCacheResponse
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Initialisation Supabase
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(
    prefix="/items",
    tags=["items"],
)

@router.get("/", response_model=List[ItemCacheResponse])
async def list_items(
    type: Optional[str] = Query(None, description="Type d'item: job, bourse, etc."),
    country: Optional[str] = Query(None, description="Filtrer par pays"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    try:
        query = supabase.table("items_cache").select("*")
        if type:
            query = query.eq("item_type", type)
        if country:
            query = query.eq("item_country", country)
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        res = query.execute()
        items = res.data or []
        return items
    except Exception as e:
        print(f"Erreur dans /items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filters")
async def get_filters():
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("[ERREUR] Variables d'environnement SUPABASE_URL ou SUPABASE_SERVICE_KEY manquantes.")
            raise HTTPException(status_code=500, detail="Configuration Supabase manquante. Contactez l'administrateur.")
        # Types de contrat
        try:
            types = supabase.table("items_cache").select("item_type").neq("item_type", None).execute().data or []
        except Exception as e:
            print(f"Erreur extraction types: {e}")
            types = []
        # Pays
        try:
            countries = supabase.table("items_cache").select("item_country").neq("item_country", None).execute().data or []
        except Exception as e:
            print(f"Erreur extraction countries: {e}")
            countries = []
        # Villes
        try:
            cities = supabase.table("items_cache").select("item_city").neq("item_city", None).execute().data or []
        except Exception as e:
            print(f"Erreur extraction cities: {e}")
            cities = []
        # Contrats
        try:
            contracts = supabase.table("items_cache").select("item_employment_type").neq("item_employment_type", None).execute().data or []
        except Exception as e:
            print(f"Erreur extraction contracts: {e}")
            contracts = []
        # Compétences (sécurisé)
        try:
            highlights = supabase.table("items_cache").select("item_highlights").execute().data or []
        except Exception as e:
            print(f"Erreur extraction highlights: {e}")
            highlights = []
        if not (types or countries or cities or contracts or highlights):
            print("[INFO] La table items_cache semble vide ou inaccessible.")
        skills_set = set()
        for h in highlights:
            try:
                if h.get("item_highlights") and isinstance(h["item_highlights"], dict):
                    qualifications = h["item_highlights"].get("qualifications")
                    if isinstance(qualifications, list):
                        for skill in qualifications:
                            if skill:
                                skills_set.add(skill.strip())
            except Exception as e:
                print(f"Erreur extraction skill: {e}")
        def unique_nonempty(values, key):
            return sorted(list(set(v[key] for v in values if v.get(key))))
        return {
            "types": unique_nonempty(types, "item_type"),
            "countries": unique_nonempty(countries, "item_country"),
            "cities": unique_nonempty(cities, "item_city"),
            "contracts": unique_nonempty(contracts, "item_employment_type"),
            "skills": sorted(list(skills_set)),
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERREUR] Exception dans /items/filters: {e}")
        return {
            "types": [],
            "countries": [],
            "cities": [],
            "contracts": [],
            "skills": [],
            "error": str(e)
        }

@router.get("/{item_id}", response_model=ItemCacheResponse)
async def get_item(item_id: str = Path(..., description="ID de l'item")):
    try:
        res = supabase.table("items_cache").select("*").eq("item_id", item_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Item non trouvé")
        return res.data
    except Exception as e:
        # Gestion spécifique de l'erreur PGRST116 (no rows or multiple rows)
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            if err.get('code') == 'PGRST116':
                raise HTTPException(status_code=404, detail="Item non trouvé")
        # Gestion du message d'erreur sous forme de dict ou str
        if hasattr(e, 'args') and e.args:
            err = e.args[0]
            if isinstance(err, dict) and err.get('message', '').startswith('JSON object requested'):
                raise HTTPException(status_code=404, detail="Item non trouvé")
            if isinstance(err, str) and 'JSON object requested' in err:
                raise HTTPException(status_code=404, detail="Item non trouvé")
        print(f"Erreur dans /items/{{item_id}}: {e}")
        raise HTTPException(status_code=500, detail=str(e))