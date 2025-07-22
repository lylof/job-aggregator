"""Prisma Database Service for job data persistence."""

import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
import structlog
import hashlib
from contextlib import asynccontextmanager

from prisma import Prisma
from prisma.errors import PrismaError

from ..config import config

logger = structlog.get_logger(__name__)


class PrismaServiceError(Exception):
    """Base exception for Prisma service-related errors."""
    pass


class PrismaService:
    """Prisma database service for job data persistence."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrismaService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not PrismaService._initialized:
            self.prisma_client = Prisma()
            self._connected = False
            logger.info("PrismaService initialized")
            PrismaService._initialized = True
    
    async def connect(self):
        """Establish connection to the database via Prisma."""
        if not self._connected:
            try:
                await self.prisma_client.connect()
                self._connected = True
                logger.info("Prisma connection established")
            except PrismaError as e:
                logger.error("Failed to connect to database via Prisma", error=str(e))
                raise PrismaServiceError(f"Prisma connection failed: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self._connected:
            await self.prisma_client.disconnect()
            self._connected = False
            logger.info("Prisma connection closed")
    
    @asynccontextmanager
    async def get_client(self):
        """Context manager for getting a connected Prisma client."""
        if not self._connected:
            await self.connect()
        try:
            yield self.prisma_client
        except PrismaError as e:
            logger.error("Prisma operation failed", error=str(e))
            raise PrismaServiceError(f"Prisma operation failed: {str(e)}")
    
    def _generate_item_id(self, source_url: str, source_site: str) -> str:
        """Generate unique item_id from URL and source."""
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]
        return f"{source_site}_{url_hash}"
    
    def _prepare_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job data for database insertion."""
        prepared_data = job_data.copy()
        
        # Generate item_id if not provided
        if 'itemId' not in prepared_data and 'item_id' not in prepared_data:
            item_id = self._generate_item_id(
                prepared_data.get('sourceUrl', prepared_data.get('source_url', '')), 
                prepared_data.get('sourceSite', prepared_data.get('source_site', 'unknown'))
            )
            prepared_data['itemId'] = item_id
        
        # Convert snake_case to camelCase if needed
        field_mappings = {
            'source_url': 'sourceUrl',
            'source_site': 'sourceSite',
            'item_id': 'itemId',
            'salary_range': 'salaryRange',
            'contract_type': 'contractType',
            'experience_level': 'experienceLevel',
            'education_level': 'educationLevel',
            'required_skills': 'requiredSkills',
            'profile_description': 'profileDescription',
            'posted_date': 'postedDate',
            'application_deadline': 'applicationDeadline',
            'contact_email': 'contactEmail',
            'contact_phone': 'contactPhone',
            'extraction_method': 'extractionMethod',
            'extraction_metadata': 'extractionMetadata',
            'quality_score': 'qualityScore',
            'raw_data': 'rawData',
            'created_at': 'createdAt',
            'updated_at': 'updatedAt',
            'is_active': 'isActive'
        }
        
        for snake_case, camel_case in field_mappings.items():
            if snake_case in prepared_data and camel_case not in prepared_data:
                prepared_data[camel_case] = prepared_data.pop(snake_case)
        
        # Handle date fields
        date_fields = ['postedDate', 'applicationDeadline']
        for field in date_fields:
            if field in prepared_data and prepared_data[field]:
                if isinstance(prepared_data[field], str):
                    try:
                        prepared_data[field] = datetime.fromisoformat(prepared_data[field])
                    except ValueError:
                        # If parsing fails, remove the field to avoid errors
                        prepared_data.pop(field)
        
        return prepared_data
    
    async def upsert_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert or update a job offer using upsert to avoid duplicates."""
        try:
            prepared_data = self._prepare_job_data(job_data)
            item_id = prepared_data.get('itemId')
            
            if not item_id:
                logger.error("Cannot upsert job without itemId")
                return None
            
            async with self.get_client() as prisma:
                job = await prisma.job.upsert(
                    where={
                        'itemId': item_id
                    },
                    data={
                        'create': prepared_data,
                        'update': prepared_data
                    }
                )
                
                logger.info("Job upserted successfully", item_id=item_id)
                return job.dict()
                
        except PrismaError as e:
            logger.error("Failed to upsert job", error=str(e))
            return None
    
    async def upsert_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert or update multiple jobs in batch."""
        if not jobs_data:
            return {"success": 0, "errors": 0, "total": 0}
        
        success_count = 0
        error_count = 0
        
        try:
            async with self.get_client() as prisma:
                # Process in smaller batches to avoid overwhelming the database
                batch_size = 50
                for i in range(0, len(jobs_data), batch_size):
                    batch = jobs_data[i:i+batch_size]
                    prepared_batch = [self._prepare_job_data(job) for job in batch]
                    
                    # Create a transaction for the batch
                    async with prisma.tx() as transaction:
                        for job_data in prepared_batch:
                            try:
                                item_id = job_data.get('itemId')
                                if not item_id:
                                    error_count += 1
                                    continue
                                
                                await transaction.job.upsert(
                                    where={
                                        'itemId': item_id
                                    },
                                    data={
                                        'create': job_data,
                                        'update': job_data
                                    }
                                )
                                success_count += 1
                            except Exception as e:
                                logger.error("Failed to upsert job in batch", error=str(e))
                                error_count += 1
            
            return {
                "success": success_count,
                "errors": error_count,
                "total": len(jobs_data)
            }
            
        except PrismaError as e:
            logger.error("Failed to batch upsert jobs", error=str(e))
            return {"success": success_count, "errors": len(jobs_data) - success_count, "total": len(jobs_data)}
    
    async def get_job_by_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Get a job by its source URL."""
        try:
            async with self.get_client() as prisma:
                job = await prisma.job.find_first(
                    where={
                        'sourceUrl': source_url
                    }
                )
                
                return job.dict() if job else None
                
        except PrismaError as e:
            logger.error("Failed to get job by URL", error=str(e))
            return None
    
    async def get_jobs_by_source(self, source_site: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs from a specific source."""
        try:
            async with self.get_client() as prisma:
                jobs = await prisma.job.find_many(
                    where={
                        'sourceSite': source_site
                    },
                    order={
                        'createdAt': 'desc'
                    },
                    take=limit
                )
                
                return [job.dict() for job in jobs]
                
        except PrismaError as e:
            logger.error("Failed to get jobs by source", error=str(e))
            return []
    
    async def update_scraping_stats(self, stats_data: Dict[str, Any]) -> bool:
        """Update scraping statistics for monitoring."""
        try:
            prepared_data = stats_data.copy()
            
            # Convert snake_case to camelCase if needed
            field_mappings = {
                'source_site': 'sourceSite',
                'scrape_date': 'scrapeDate',
                'urls_discovered': 'urlsDiscovered',
                'urls_processed': 'urlsProcessed',
                'jobs_created': 'jobsCreated',
                'jobs_updated': 'jobsUpdated',
                'success_rate': 'successRate',
                'processing_time_seconds': 'processingTimeSeconds',
                'errors_count': 'errorsCount',
                'error_details': 'errorDetails',
                'created_at': 'createdAt'
            }
            
            for snake_case, camel_case in field_mappings.items():
                if snake_case in prepared_data and camel_case not in prepared_data:
                    prepared_data[camel_case] = prepared_data.pop(snake_case)
            
            # Handle date fields
            if 'scrapeDate' in prepared_data:
                if isinstance(prepared_data['scrapeDate'], str):
                    prepared_data['scrapeDate'] = datetime.fromisoformat(prepared_data['scrapeDate'])
                elif isinstance(prepared_data['scrapeDate'], date):
                    prepared_data['scrapeDate'] = datetime.combine(prepared_data['scrapeDate'], datetime.min.time())
            
            source_site = prepared_data.get('sourceSite')
            scrape_date = prepared_data.get('scrapeDate')
            
            if not source_site or not scrape_date:
                logger.error("Cannot update scraping stats without sourceSite and scrapeDate")
                return False
            
            async with self.get_client() as prisma:
                stats = await prisma.scrapingstat.upsert(
                    where={
                        'sourceSite_scrapeDate': {
                            'sourceSite': source_site,
                            'scrapeDate': scrape_date
                        }
                    },
                    data={
                        'create': prepared_data,
                        'update': prepared_data
                    }
                )
                
                return bool(stats)
                
        except PrismaError as e:
            logger.error("Failed to update scraping stats", error=str(e))
            return False