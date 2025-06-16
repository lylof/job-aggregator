import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis dans l'environnement")
    return create_client(supabase_url, supabase_key) 