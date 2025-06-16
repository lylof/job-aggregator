import os
 
def get_jsearch_api_key():
    key = os.environ.get("JSEARCH_API_KEY")
    if not key:
        raise RuntimeError("JSEARCH_API_KEY n'est pas défini dans les variables d'environnement.")
    return key 