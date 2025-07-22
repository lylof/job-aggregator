"""Data models for Jina Job Scraper using Pydantic."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class ExtractionMethod(str, Enum):
    """Methods used for job data extraction."""
    JINA = "jina"
    GEMINI = "gemini"
    CRAWL4AI = "crawl4ai"
    MANUAL = "manual"


class JobType(str, Enum):
    """Types of job positions."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    TEMPORARY = "temporary"


class SalaryPeriod(str, Enum):
    """Salary payment periods."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SalaryRange(BaseModel):
    """Salary range information."""
    min_amount: Optional[float] = Field(None, description="Minimum salary amount")
    max_amount: Optional[float] = Field(None, description="Maximum salary amount")
    currency: str = Field(default="XOF", description="Currency code (default: West African CFA franc)")
    period: SalaryPeriod = Field(default=SalaryPeriod.MONTHLY, description="Payment period")
    is_negotiable: bool = Field(default=False, description="Whether salary is negotiable")
    
    @validator('max_amount')
    def validate_salary_range(cls, v, values):
        """Ensure max_amount is greater than min_amount if both are provided."""
        if v is not None and values.get('min_amount') is not None:
            if v < values['min_amount']:
                raise ValueError('max_amount must be greater than min_amount')
        return v


class JobLocation(BaseModel):
    """Job location information."""
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="Region/state name")
    country: str = Field(default="Togo", description="Country name")
    is_remote: bool = Field(default=False, description="Whether job allows remote work")
    address: Optional[str] = Field(None, description="Full address if available")


class CompanyInfo(BaseModel):
    """Company information."""
    name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Industry sector")
    size: Optional[str] = Field(None, description="Company size (e.g., '10-50 employees')")
    website: Optional[HttpUrl] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description")


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""
    method: ExtractionMethod = Field(..., description="Extraction method used")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When data was extracted")
    source_site: str = Field(..., description="Source job site name")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    enriched_fields: List[str] = Field(default_factory=list, description="Fields enhanced by AI")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class JobOffer(BaseModel):
    """Main job offer model with all required and optional fields."""
    
    # Required fields
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    source_url: HttpUrl = Field(..., description="Original job posting URL")
    extraction_method: ExtractionMethod = Field(..., description="How the data was extracted")
    
    # Optional but preferred fields
    description: Optional[str] = Field(None, description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    location: Optional[JobLocation] = Field(None, description="Job location details")
    salary_range: Optional[SalaryRange] = Field(None, description="Salary information")
    job_type: Optional[JobType] = Field(None, description="Type of employment")
    posted_date: Optional[datetime] = Field(None, description="When job was posted")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    
    # Company information
    company_info: Optional[CompanyInfo] = Field(None, description="Detailed company information")
    
    # Technical fields
    extraction_metadata: ExtractionMetadata = Field(..., description="Extraction process metadata")
    tags: List[str] = Field(default_factory=list, description="Job tags/keywords")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw extracted data for debugging")
    
    # Database fields (will be set by the storage service)
    id: Optional[str] = Field(None, description="Database ID")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    
    @validator('posted_date', 'application_deadline')
    def validate_dates_not_future(cls, v):
        """Ensure dates are not in the future."""
        if v is not None and v > datetime.utcnow():
            raise ValueError('Date cannot be in the future')
        return v
    
    @validator('application_deadline')
    def validate_deadline_after_posted(cls, v, values):
        """Ensure application deadline is after posted date."""
        if v is not None and values.get('posted_date') is not None:
            if v < values['posted_date']:
                raise ValueError('Application deadline must be after posted date')
        return v


class JobOfferBatch(BaseModel):
    """Batch of job offers for bulk processing."""
    jobs: List[JobOffer] = Field(..., description="List of job offers")
    batch_id: str = Field(..., description="Unique batch identifier")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Batch processing timestamp")
    source_site: str = Field(..., description="Source site for this batch")
    total_count: int = Field(..., description="Total number of jobs in batch")
    
    @validator('total_count')
    def validate_count_matches_jobs(cls, v, values):
        """Ensure total_count matches actual job count."""
        if 'jobs' in values and len(values['jobs']) != v:
            raise ValueError('total_count must match the number of jobs')
        return v


class ScrapingResult(BaseModel):
    """Result of a scraping operation."""
    success: bool = Field(..., description="Whether scraping was successful")
    jobs_found: int = Field(default=0, description="Number of jobs found")
    jobs_processed: int = Field(default=0, description="Number of jobs successfully processed")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    processing_time_seconds: float = Field(..., description="Total processing time")
    source_site: str = Field(..., description="Source site scraped")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Scraping timestamp")