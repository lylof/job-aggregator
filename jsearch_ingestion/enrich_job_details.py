import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement (.env)
load_dotenv()

SUPABASE_URL = "https://bttnfynoxbxynuwqrdpm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0dG5meW5veGJ4eW51d3FyZHBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5NDM4MzcsImV4cCI6MjA2NTUxOTgzN30.beS4cMdznno4Yzb_iVGkPJ3AgTatB4B4ibDPuBdatFc"
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fonction pour appeler l'API JSearch /job-details
def fetch_job_details(job_id):
    url = "https://jsearch.p.rapidapi.com/job-details"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"job_id": job_id}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def enrich_offer_with_details(job_id, force_refresh=False):
    # Vérifier si déjà détaillé et récent
    res = supabase.table("items_cache").select("job_detailed, details_fetched_at").eq("item_id", job_id).single().execute()
    data = res.data
    if data:
        if data.get("job_detailed") and not force_refresh:
            # Vérifier si le détail est récent (< 7 jours)
            fetched_at = data.get("details_fetched_at")
            if fetched_at:
                fetched_dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                if fetched_dt > datetime.now(timezone.utc) - timedelta(days=7):
                    print(f"Déjà détaillé et récent pour {job_id}, skip.")
                    return
    # Appel API JSearch
    details = fetch_job_details(job_id)
    supabase.table("items_cache").update({
        "job_full_data": details,
        "job_detailed": True,
        "details_fetched_at": datetime.now(timezone.utc).isoformat()
    }).eq("item_id", job_id).execute()
    print(f"Détails enrichis pour {job_id}")

if __name__ == "__main__":
    # Exemple d'utilisation : enrichir une offre précise
    job_id = input("Entrer le job_id à enrichir : ")
    enrich_offer_with_details(job_id) 