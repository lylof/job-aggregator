from dotenv import load_dotenv
load_dotenv()

import os
from .config import get_jsearch_api_key
from .transform import transform_jsearch_job
import requests
import json

def fetch_and_transform_jobs(query, country="fr", page=1, num_pages=1):
    api_key = get_jsearch_api_key()
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": query,
        "country": country,
        "page": page,
        "num_pages": num_pages
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    jobs = [transform_jsearch_job(j) for j in data.get("data", [])]
    return jobs

def main():
    jobs = fetch_and_transform_jobs("emploi Togo", country="TG", page=1, num_pages=2)
    print(json.dumps(jobs, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 