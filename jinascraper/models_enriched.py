"""
Enhanced data models for Phase 2 Enhanced Data Pipeline.
These models extend the existing models.py without breaking compatibility.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

class ChunkType(Enum):
    """Types of content chunks for semantic segmentation."""
    TITLE = "title"
    DESCRIPTION = "description"
    REQUIREMENTS = "requirements"
    COMPENSATION = "compensation"
    COMPANY_INFO = "company_info"
    LOCATION = "location"
    APPLICATION = "application"
    OTHER = "other"

class ExtractionMethod(Enum):
    """Methods used for data extraction."""
    JINA_ENHANCED = "jina_enhanced"
    JINA_FALLBACK = "jina_fallback"
    MANUAL_EXTRACTION = "manual_extraction"

@dataclass
class ContentChunk:
    """
    Individual content chunk with semantic metadata.
    Used for Phase 2.2 advanced features (Segmenter + Embeddings).
    """
    text: str
    chunk_index: int
    chunk_type: ChunkType
    token_count: int
    confidence_score: float
    source_url: str
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process."""
    extraction_timestamp: datetime
    processing_duration_ms: int
    content_length: int
    content_quality_score: float
    source_site: str
    jina_model_version: str
    extraction_method: ExtractionMethod

@dataclass
class PipelineMetadata:
    """Metadata about the processing pipeline for observability."""
    reader_duration_ms: int
    segmenter_duration_ms: Optional[int] = None  # Phase 2.2
    embeddings_duration_ms: Optional[int] = None  # Phase 2.2
    gemini_duration_ms: Optional[int] = None
    total_api_calls: int = 0
    total_cost_usd: float = 0.0
    pipeline_version: str = "2.1"

@dataclass
class Stage2StructuredData:
    """
    Comprehensive structured data schema for job offers.
    This is the JSON structure that Gemini will populate.
    """
    # Basic information
    title: Optional[str] = None
    company: Optional[str] = None
    
    # Location information
    location: Optional[Dict[str, str]] = None  # {"city": "Lomé", "region": "Maritime", "country": "Togo"}
    
    # Contract details
    contract: Optional[Dict[str, Any]] = None  # {"type": "CDI", "duration": null, "start_date": "2025-02-01"}
    
    # Salary information
    salary: Optional[Dict[str, Any]] = None  # {"min": 150000, "max": 200000, "currency": "XOF", "period": "monthly", "negotiable": false}
    
    # Requirements
    requirements: Optional[Dict[str, Any]] = None  # {"experience": "2-3 ans", "education": "Bac+3", "skills": [...], "languages": [...]}
    
    # Detailed description
    description: Optional[Dict[str, Any]] = None  # {"summary": "...", "missions": [...], "profile": "...", "benefits": [...]}
    
    # Application information
    application: Optional[Dict[str, Any]] = None  # {"deadline": "2025-03-01", "email": "...", "phone": "...", "instructions": "..."}
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None  # {"publication_date": "2025-01-15", "sector": "IT", "department": "Développement"}

@dataclass
class EnrichedJobData:
    """
    Complete enriched job data object - the main deliverable of Phase 2.
    This represents a job that has been processed through Stage 2.
    """
    # Identifiers
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_url: str = ""
    
    # Raw data from Stage 2
    stage2_markdown: str = ""
    stage2_structured: Dict[str, Any] = field(default_factory=dict)
    processing_stage: str = "stage2"
    
    # Processing metadata
    stage2_processed_at: datetime = field(default_factory=datetime.utcnow)
    stage2_processing_time_ms: int = 0
    extraction_quality_score: float = 0.0
    
    # Phase 2.2 fields (for future use)
    content_chunks: Optional[List[ContentChunk]] = None
    description_embedding: Optional[List[float]] = None
    
    # Validation and quality
    validation_errors: List[str] = field(default_factory=list)
    extraction_metadata: Optional[ExtractionMetadata] = None
    pipeline_metadata: Optional[PipelineMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "job_id": self.job_id,
            "source_url": self.source_url,
            "stage2_markdown": self.stage2_markdown,
            "stage2_structured": self.stage2_structured,
            "processing_stage": self.processing_stage,
            "stage2_processed_at": self.stage2_processed_at,
            "stage2_processing_time_ms": self.stage2_processing_time_ms,
            "extraction_quality_score": self.extraction_quality_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnrichedJobData':
        """Create from dictionary (database retrieval)."""
        return cls(
            job_id=data.get("job_id", str(uuid.uuid4())),
            source_url=data.get("source_url", ""),
            stage2_markdown=data.get("stage2_markdown", ""),
            stage2_structured=data.get("stage2_structured", {}),
            processing_stage=data.get("processing_stage", "stage2"),
            stage2_processed_at=data.get("stage2_processed_at", datetime.utcnow()),
            stage2_processing_time_ms=data.get("stage2_processing_time_ms", 0),
            extraction_quality_score=data.get("extraction_quality_score", 0.0)
        )

@dataclass
class EnhancedPipelineResult:
    """Result object for enhanced pipeline execution."""
    enriched_jobs: List[EnrichedJobData]
    pipeline_metrics: Dict[str, Any]
    success: bool
    total_duration_seconds: float
    
    # Summary statistics
    total_urls_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    average_quality_score: float = 0.0
    total_cost_usd: float = 0.0
    
    def __post_init__(self):
        """Calculate summary statistics."""
        self.successful_extractions = len(self.enriched_jobs)
        self.total_urls_processed = self.successful_extractions + self.failed_extractions
        if self.enriched_jobs:
            self.average_quality_score = sum(
                job.extraction_quality_score for job in self.enriched_jobs
            ) / len(self.enriched_jobs)

@dataclass
class DeduplicationMetrics:
    """Metrics for semantic deduplication (Phase 2.2)."""
    total_jobs: int
    unique_jobs: int
    duplicates_found: int
    deduplication_rate: float
    similarity_threshold: float = 0.85

# Validation schemas and helpers
def validate_stage2_structured_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate Stage 2 structured data against expected schema.
    Args:
        data: The structured data dictionary from Gemini
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ["title", "company"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate location structure if present
    if "location" in data and data["location"]:
        location = data["location"]
        if not isinstance(location, dict):
            errors.append("Location must be a dictionary")
        elif "country" in location and location["country"] != "Togo":
            errors.append("Country should be 'Togo' for Togo job sources")
    
    # Validate salary structure if present
    if "salary" in data and data["salary"]:
        salary = data["salary"]
        if not isinstance(salary, dict):
            errors.append("Salary must be a dictionary")
        elif "currency" in salary and salary["currency"] not in ["XOF", "EUR", "USD"]:
            errors.append("Currency should be XOF, EUR, or USD")
    
    # Validate contract structure if present
    if "contract" in data and data["contract"]:
        contract = data["contract"]
        if not isinstance(contract, dict):
            errors.append("Contract must be a dictionary")
        elif "type" in contract and contract["type"] not in ["CDI", "CDD", "Stage", "Freelance", "Intérim"]:
            errors.append("Contract type should be CDI, CDD, Stage, Freelance, or Intérim")
    
    return errors

def calculate_data_quality_score(structured_data: Dict[str, Any]) -> float:
    """
    Calculate quality score based on data completeness and validity.
    Args:
        structured_data: The structured data from Gemini
    Returns:
        Quality score between 0.0 and 1.0
    """
    if not structured_data:
        return 0.0
    
    # Field weights (total should be 1.0)
    field_weights = {
        "title": 0.2,
        "company": 0.2,
        "location": 0.15,
        "contract": 0.1,
        "salary": 0.1,
        "requirements": 0.1,
        "description": 0.1,
        "application": 0.05
    }
    
    score = 0.0
    for field, weight in field_weights.items():
        if field in structured_data and structured_data[field]:
            field_value = structured_data[field]
            # Bonus for complex objects with multiple sub-fields
            if isinstance(field_value, dict):
                sub_fields = len([v for v in field_value.values() if v])
                # Normalize: 1-3 sub-fields = partial credit, 4+ = full credit
                field_score = min(1.0, sub_fields / 3.0)
                score += weight * field_score
            elif isinstance(field_value, list):
                # For lists, give credit based on number of items
                list_score = min(1.0, len(field_value) / 3.0)
                score += weight * list_score
            else:
                # Simple field with value
                score += weight
    
    return round(score, 2)

# Export all classes and functions
__all__ = [
    'ChunkType',
    'ExtractionMethod', 
    'ContentChunk',
    'ExtractionMetadata',
    'PipelineMetadata',
    'Stage2StructuredData',
    'EnrichedJobData',
    'EnhancedPipelineResult',
    'DeduplicationMetrics',
    'validate_stage2_structured_data',
    'calculate_data_quality_score'
]