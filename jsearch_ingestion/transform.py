from datetime import datetime

def transform_jsearch_job(job: dict) -> dict:
    # Mapping minimal, à enrichir selon le schéma items_cache du PRD
    return {
        "item_id": job.get("job_id"),
        "item_provider": "jsearch",
        "item_type": "job",
        "source_type": "api",
        "source_name": "jsearch",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "item_posted_at": job.get("job_posted_at_datetime_utc"),
        "item_expires_at": job.get("job_offer_expiration_datetime_utc"),
        "item_title": job.get("job_title"),
        "company_name": job.get("employer_name"),
        "item_employment_type": job.get("job_employment_type"),
        "item_is_remote": job.get("job_is_remote"),
        "item_city": job.get("job_city"),
        "item_state": job.get("job_state"),
        "item_country": job.get("job_country"),
        "item_latitude": job.get("job_latitude"),
        "item_longitude": job.get("job_longitude"),
        "item_description": job.get("job_description"),
        "item_highlights": job.get("job_highlights"),
        "raw_data": job,
        "is_active": True
    } 