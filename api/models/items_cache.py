from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ItemCacheBase(BaseModel):
    item_id: str
    item_provider: str
    item_type: str = 'job'  # 'job', 'bourse', etc.
    source_type: str  # 'api', 'rss', 'direct'
    source_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    item_posted_at: Optional[datetime] = None
    item_expires_at: Optional[datetime] = None
    item_title: Optional[str] = None
    company_name: Optional[str] = None
    item_employment_type: Optional[str] = None
    item_is_remote: Optional[bool] = False
    item_city: Optional[str] = None
    item_state: Optional[str] = None
    item_country: Optional[str] = None
    item_latitude: Optional[float] = None
    item_longitude: Optional[float] = None
    item_description: Optional[str] = None
    item_highlights: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any]
    sync_batch_id: Optional[str] = None
    is_active: Optional[bool] = True
    # Champs d'enrichissement (optionnels)
    job_detailed: Optional[bool] = None
    details_fetched_at: Optional[datetime] = None
    job_full_data: Optional[Dict[str, Any]] = None

class ItemCacheResponse(ItemCacheBase):
    pass 