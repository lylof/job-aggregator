"""Supabase Database Service for job data persistence with field mapping."""

import hashlib
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import structlog

from ..config import config
try:
    from .field_mapper import FieldMapper, FieldMappingError
    from ..utils.schema_validator import SchemaValidator, SchemaValidationError
except ImportError:
    # Fallback pour les tests directs
    from field_mapper import FieldMapper, FieldMappingError
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from utils.schema_validator import SchemaValidator, SchemaValidationError


logger = structlog.get_logger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class DatabaseService:
    """Enhanced Supabase database service with field mapping and validation."""
    
    def __init__(self):
        self.supabase_url = config.supabase_url
        self.supabase_key = config.supabase_key
        self.supabase_client = None
        
        # Initialize field mapping and validation services
        self.field_mapper = FieldMapper()
        self.schema_validator = SchemaValidator()
        
        logger.info("DatabaseService initialized with field mapping",
                   field_mapper=True,
                   schema_validator=True)
    
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
    
    def _prepare_job_data(self, job_data: Dict[str, Any], source_name: str = None) -> Dict[str, Any]:
        """Enhanced preparation with field mapping and validation + raw_text support + safe extraction_method."""
        try:
            job_url = job_data.get('source_url', 'unknown')

            logger.debug("Starting job data preparation",
                         job_url=job_url,
                         source=source_name,
                         original_fields=len(job_data))

            # 1) Field mapping (ex: profile -> profile_description)
            mapped_data = self.field_mapper.map_job_fields(job_data.copy(), source_name)

            # 1.1) Robust raw_text extraction (clean human-readable text)
            # Prefer explicit clean_text, then text; fallback: try to derive from raw_data.content if it's a string.
            raw_text_value = None
            try:
                raw_payload = mapped_data.get("raw_data") or job_data.get("raw_data") or {}
                if isinstance(raw_payload, dict):
                    if isinstance(raw_payload.get("clean_text"), str) and raw_payload.get("clean_text").strip():
                        raw_text_value = raw_payload.get("clean_text").strip()
                    elif isinstance(raw_payload.get("text"), str) and raw_payload.get("text").strip():
                        raw_text_value = raw_payload.get("text").strip()
                    elif isinstance(raw_payload.get("content"), str) and raw_payload.get("content").strip():
                        # Many extractors store cleaned markdown/text as "content"
                        raw_text_value = raw_payload.get("content").strip()
                elif isinstance(raw_payload, str) and raw_payload.strip():
                    # Edge case: raw_data provided directly as string
                    raw_text_value = raw_payload.strip()
            except Exception as _:
                # Do not fail the pipeline for raw text extraction
                raw_text_value = None

            if raw_text_value:
                mapped_data["raw_text"] = raw_text_value

            logger.info("Field mapping applied successfully",
                        job_url=job_url,
                        source=source_name,
                        mapped_fields=len(mapped_data))

            # 2) Normalize/accept extraction_method and annotate fallback when applicable
            # Allowed by DB constraint now: 'jina','gemini','crawl4ai','manual','raw_only'
            method = mapped_data.get("extraction_method")
            if method == "raw_only":
                meta = mapped_data.get("extraction_metadata") or {}
                if isinstance(meta, dict):
                    meta.setdefault("fallback", "raw_only")
                    mapped_data["extraction_metadata"] = meta
            # Ensure method is present; default to 'jina' if missing
            if not method:
                mapped_data["extraction_method"] = "jina"

            # 3) Validate schema compatibility
            validated_data = self.schema_validator.validate_complete_job(mapped_data, job_url)

            logger.info("Schema validation passed",
                        job_url=job_url,
                        valid_fields=len(validated_data))

            # 4) Generate item_id if not present
            if 'item_id' not in validated_data:
                validated_data['item_id'] = self._generate_item_id(
                    validated_data['source_url'],
                    validated_data.get('source_site', 'unknown')
                )

            # 5) Convert datetime objects to ISO format strings
            prepared_data = self._convert_datetime_fields(validated_data)

            logger.info("Job data preparation completed successfully",
                        job_url=job_url,
                        source=source_name,
                        final_fields=len(prepared_data))

            return prepared_data

        except (FieldMappingError, SchemaValidationError) as e:
            logger.error("Job data preparation failed",
                        job_url=job_data.get('source_url', 'unknown'),
                        source=source_name,
                        error=str(e))
            raise DatabaseError(f"Data preparation failed: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in job data preparation",
                        job_url=job_data.get('source_url', 'unknown'),
                        source=source_name,
                        error=str(e))
            raise DatabaseError(f"Unexpected preparation error: {str(e)}")
    
    def _convert_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime objects to ISO format strings recursively."""
        import json
        
        def convert_value(value):
            """Recursively convert datetime objects to ISO strings."""
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            else:
                return value
        
        converted_data = {}
        for key, value in data.items():
            converted_data[key] = convert_value(value)
        
        # Test JSON serialization to catch any remaining issues
        try:
            json.dumps(converted_data, ensure_ascii=False)
        except TypeError as e:
            logger.error("JSON serialization failed after datetime conversion", 
                        error=str(e), 
                        problematic_keys=[k for k, v in converted_data.items() 
                                        if not isinstance(v, (str, int, float, bool, list, dict, type(None)))])
            raise DatabaseError(f"Data serialization failed: {str(e)}")
        
        return converted_data
    
    async def upsert_job(self, job_data: Dict[str, Any], source_name: str = None) -> Optional[Dict[str, Any]]:
        """Insert or update a job offer with enhanced field mapping."""
        try:
            if not self.supabase_client:
                self.connect()
            
            # Enhanced preparation with field mapping and validation
            prepared_data = self._prepare_job_data(job_data.copy(), source_name)
            
            result = self.supabase_client.table('jobs').upsert(
                prepared_data,
                on_conflict='item_id'
            ).execute()
            
            if result.data:
                job_record = result.data[0]
                logger.info("Job upserted successfully with field mapping",
                           item_id=job_record.get('item_id'),
                           source=source_name,
                           job_url=job_data.get('source_url'))
                return job_record
            
            return None
                
        except DatabaseError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error("Failed to upsert job",
                        job_url=job_data.get('source_url', 'unknown'),
                        source=source_name,
                        error=str(e))
            return None
    
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]], source_name: str = None) -> Dict[str, Any]:
        """Insert or update multiple jobs in batch with enhanced field mapping."""
        try:
            if not self.supabase_client:
                self.connect()
            
            if not jobs_data:
                return {"success": 0, "errors": 0, "total": 0, "mapping_errors": 0}
            
            logger.info("Starting batch job preparation with field mapping",
                       total_jobs=len(jobs_data),
                       source=source_name)
            
            prepared_jobs = []
            mapping_errors = 0
            
            # Prepare each job with field mapping and validation
            for job_data in jobs_data:
                try:
                    prepared_job = self._prepare_job_data(job_data.copy(), source_name)
                    prepared_jobs.append(prepared_job)
                except DatabaseError as e:
                    mapping_errors += 1
                    logger.warning("Job preparation failed, skipping job",
                                 job_url=job_data.get('source_url', 'unknown'),
                                 source=source_name,
                                 error=str(e))
            
            if not prepared_jobs:
                logger.error("No jobs could be prepared for batch upsert",
                           total_jobs=len(jobs_data),
                           mapping_errors=mapping_errors)
                return {"success": 0, "errors": len(jobs_data), "total": len(jobs_data), "mapping_errors": mapping_errors}
            
            # Batch upsert to Supabase
            result = self.supabase_client.table('jobs').upsert(
                prepared_jobs,
                on_conflict='item_id'
            ).execute()
            
            success_count = len(result.data) if result.data else 0
            
            logger.info("Batch upsert completed with field mapping",
                       total_jobs=len(jobs_data),
                       prepared_jobs=len(prepared_jobs),
                       success_count=success_count,
                       mapping_errors=mapping_errors,
                       source=source_name)
            
            return {
                "success": success_count,
                "errors": len(prepared_jobs) - success_count,
                "total": len(jobs_data),
                "mapping_errors": mapping_errors,
                "prepared_jobs": len(prepared_jobs)
            }
            
        except Exception as e:
            logger.error("Failed to batch upsert jobs with field mapping",
                        total_jobs=len(jobs_data),
                        source=source_name,
                        error=str(e))
            return {"success": 0, "errors": len(jobs_data), "total": len(jobs_data), "mapping_errors": 0}
    
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