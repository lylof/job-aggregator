from supabase import create_client, Client
import os
from dotenv import load_dotenv
from jsearch_ingestion.main import fetch_and_transform_jobs

# Charger les variables d'environnement (.env)
load_dotenv()

SUPABASE_URL = "https://bttnfynoxbxynuwqrdpm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0dG5meW5veGJ4eW51d3FyZHBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5NDM4MzcsImV4cCI6MjA2NTUxOTgzN30.beS4cMdznno4Yzb_iVGkPJ3AgTatB4B4ibDPuBdatFc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def export_jobs_to_supabase():
    jobs = fetch_and_transform_jobs("emploi Togo", country="TG", page=1, num_pages=2)
    for job in jobs:
        try:
            response = supabase.table("items_cache").upsert(job).execute()
            print(f"Upserted: {job['item_id']} | Response: {response}")
        except Exception as e:
            print(f"Erreur lors de l'upsert de {job['item_id']}: {e}")

if __name__ == "__main__":
    export_jobs_to_supabase() 