"""Supabase Database Service for job data persistence."""

import hashlib
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import structlog

from ..config import config


logger = structlog.get_logger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class DatabaseService:
    """Supabase database service for job data persistence."""
    
    def __init__(self):
        self.supabase_url = config.supabase_url
        self.supabase_key = config.supabase_key
        self.supabase_client = None
        
        logger.info("DatabaseService initialized")
    
    def connect(self):
        """Establish connection to Supabase."""
        try:
            from supabase import create_client
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase connection established")
            
        except Exception as e:
            logger.error("Failed to connect to Supabase", error=str(e))
            raise DatabaseError(f"Supabase connection failed: {str(e)}")
    
    def _generate_item_id(self, source_url: str, source_site: str) -> str:
        """Generate unique item_id from URL and source."""
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]
        return f"{source_site}_{url_hash}"
    
    def _prepare_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job data for database insertion."""
        if 'item_id' not in job_data:
            job_data['item_id'] = self._generate_item_id(
                job_data['source_url'], 
                job_data.get('source_site', 'unknown')
            )
        
        for date_field in ['posted_date', 'application_deadline']:
            if date_field in job_data and job_data[date_field]:
                if isinstance(job_data[date_field], (datetime, date)):
                    job_data[date_field] = job_data[date_field].isoformat()
        
        return job_data
    
    async def upsert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert or update a job offer using upsert to avoid duplicates."""
        try:
            if not self.supabase_client:
                self.connect()
            
            prepared_data = self._prepare_job_data(job_data.copy())
            
            result = self.supabase_client.table('jobs').upsert(
                prepared_data,
                on_conflict='item_id'
            ).execute()
            
            if result.data:
                job_record = result.data[0]
                logger.info("Job upserted successfully", item_id=job_record.get('item_id'))
                return job_record
            
            return None
                
        except Exception as e:
            logger.error("Failed to upsert job", error=str(e))
            return None
    
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert or update multiple jobs in batch."""
        try:
            if not self.supabase_client:
                self.connect()
            
            if not jobs_data:
                return {"success": 0, "errors": 0, "total": 0}
            
            prepared_jobs = [self._prepare_job_data(job.copy()) for job in jobs_data]
            
            result = self.supabase_client.table('jobs').upsert(
                prepared_jobs,
                on_conflict='item_id'
            ).execute()
            
            return {
                "success": len(result.data) if result.data else 0,
                "errors": len(prepared_jobs) - (len(result.data) if result.data else 0),
                "total": len(prepared_jobs)
            }
            
        except Exception as e:
            logger.error("Failed to batch upsert jobs", error=str(e))
            return {"success": 0, "errors": len(jobs_data), "total": len(jobs_data)}
    
    async def get_job_by_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Get a job by its source URL."""
        try:
            if not self.supabase_client:
                self.connect()
            
            result = self.supabase_client.table('jobs').select('*').eq(
                'source_url', source_url
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error("Failed to get job by URL", error=str(e))
            return None
    
    async def get_jobs_by_source(self, source_site: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs from a specific source."""
        try:
            if not self.supabase_client:
                self.connect()
            
            result = self.supabase_client.table('jobs').select('*').eq(
                'source_site', source_site
            ).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error("Failed to get jobs by source", error=str(e))
            return []
    
    async def update_scraping_stats(self, stats_data: Dict[str, Any]) -> bool:
        """Update scraping statistics for monitoring."""
        try:
            if not self.supabase_client:
                self.connect()
            
            if isinstance(stats_data.get('scrape_date'), date):
                stats_data['scrape_date'] = stats_data['scrape_date'].isoformat()
            
            result = self.supabase_client.table('scraping_stats').upsert(
                stats_data,
                on_conflict='source_site,scrape_date'
            ).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error("Failed to update scraping stats", error=str(e))
            return False