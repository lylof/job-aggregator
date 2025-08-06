"""Schema Validator for JinaScraper - Validates data against Supabase schema."""

from typing import Dict, Any, Set, List, Optional
import structlog
from datetime import datetime, date

logger = structlog.get_logger(__name__)


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class SchemaValidator:
    """Validates data against Supabase schema with detailed logging."""
    
    # Colonnes valides de la table jobs (basé sur le schéma Supabase réel)
    VALID_COLUMNS = {
        'id', 'item_id', 'title', 'company', 'source_url', 'source_site',
        'description', 'location', 'salary_range', 'contract_type',
        'experience_level', 'education_level', 'sector', 'missions',
        'required_skills', 'profile_description', 'posted_date',
        'application_deadline', 'contact_email', 'contact_phone',
        'extraction_method', 'extraction_metadata', 'quality_score',
        'raw_data', 'created_at', 'updated_at', 'is_active'
    }
    
    # Champs requis pour une sauvegarde réussie
    REQUIRED_FIELDS = {
        'title', 'company', 'source_url', 'extraction_method'
    }
    
    # Champs de type array
    ARRAY_FIELDS = {
        'missions', 'required_skills'
    }
    
    # Champs de type date
    DATE_FIELDS = {
        'posted_date', 'application_deadline', 'created_at', 'updated_at'
    }
    
    # Champs de type JSONB
    JSON_FIELDS = {
        'extraction_metadata', 'raw_data'
    }
    
    def __init__(self):
        """Initialize the SchemaValidator."""
        logger.info("SchemaValidator initialized",
                   valid_columns=len(self.VALID_COLUMNS),
                   required_fields=len(self.REQUIRED_FIELDS))
    
    def filter_valid_fields(self, data: Dict[str, Any], job_url: str = None) -> Dict[str, Any]:
        """
        Remove invalid fields and log warnings with job URL context.
        
        Args:
            data: Job data to filter
            job_url: Job URL for logging context
            
        Returns:
            Filtered data with only valid fields
        """
        try:
            valid_data = {}
            invalid_fields = []
            
            for field, value in data.items():
                if field in self.VALID_COLUMNS:
                    # Validate field type and format
                    validated_value = self._validate_field_value(field, value)
                    if validated_value is not None:
                        valid_data[field] = validated_value
                    else:
                        invalid_fields.append(f"{field} (invalid value)")
                else:
                    invalid_fields.append(field)
            
            # Log invalid fields with context
            if invalid_fields:
                logger.warning("Invalid fields filtered out",
                             job_url=job_url,
                             invalid_fields=invalid_fields,
                             invalid_count=len(invalid_fields),
                             valid_count=len(valid_data))
            
            logger.debug("Field filtering completed",
                        job_url=job_url,
                        original_fields=len(data),
                        valid_fields=len(valid_data),
                        filtered_fields=len(invalid_fields))
            
            return valid_data
            
        except Exception as e:
            logger.error("Field filtering failed",
                        job_url=job_url,
                        error=str(e))
            raise SchemaValidationError(f"Field filtering failed: {str(e)}")
    
    def _validate_field_value(self, field: str, value: Any) -> Any:
        """
        Validate field value according to its expected type.
        
        Args:
            field: Field name
            value: Field value
            
        Returns:
            Validated value or None if invalid
        """
        try:
            # Skip None values (they're valid for optional fields)
            if value is None:
                return None
            
            # Validate array fields
            if field in self.ARRAY_FIELDS:
                if isinstance(value, list):
                    # Ensure all items are strings
                    return [str(item) for item in value if item is not None]
                elif isinstance(value, str):
                    # Convert string to single-item array
                    return [value]
                else:
                    logger.warning("Invalid array field value",
                                 field=field,
                                 value_type=type(value).__name__)
                    return None
            
            # Validate date fields
            if field in self.DATE_FIELDS:
                if isinstance(value, (datetime, date)):
                    return value
                elif isinstance(value, str):
                    # Try to parse ISO format
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        logger.warning("Invalid date format",
                                     field=field,
                                     value=value)
                        return None
                else:
                    logger.warning("Invalid date field value",
                                 field=field,
                                 value_type=type(value).__name__)
                    return None
            
            # Validate JSON fields
            if field in self.JSON_FIELDS:
                if isinstance(value, (dict, list)):
                    return value
                else:
                    logger.warning("Invalid JSON field value",
                                 field=field,
                                 value_type=type(value).__name__)
                    return None
            
            # For other fields, convert to string if not already
            if isinstance(value, str):
                return value
            else:
                return str(value)
                
        except Exception as e:
            logger.warning("Field value validation failed",
                         field=field,
                         error=str(e))
            return None
    
    def validate_required_fields(self, data: Dict[str, Any], job_url: str = None) -> bool:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            data: Job data to validate
            job_url: Job URL for logging context
            
        Returns:
            True if all required fields are present
        """
        missing_fields = []
        empty_fields = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                missing_fields.append(field)
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                empty_fields.append(field)
        
        if missing_fields or empty_fields:
            logger.error("Required field validation failed",
                        job_url=job_url,
                        missing_fields=missing_fields,
                        empty_fields=empty_fields)
            return False
        
        logger.debug("Required field validation passed",
                    job_url=job_url,
                    required_fields=list(self.REQUIRED_FIELDS))
        return True
    
    def validate_complete_job(self, data: Dict[str, Any], job_url: str = None) -> Dict[str, Any]:
        """
        Complete validation: filter fields + validate required fields.
        
        Args:
            data: Job data to validate
            job_url: Job URL for logging context
            
        Returns:
            Validated and filtered job data
            
        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            # 1. Filter valid fields
            valid_data = self.filter_valid_fields(data, job_url)
            
            # 2. Validate required fields
            if not self.validate_required_fields(valid_data, job_url):
                raise SchemaValidationError(
                    f"Required field validation failed for job: {job_url}"
                )
            
            logger.info("Complete job validation successful",
                       job_url=job_url,
                       valid_fields=len(valid_data))
            
            return valid_data
            
        except SchemaValidationError:
            raise
        except Exception as e:
            logger.error("Complete job validation failed",
                        job_url=job_url,
                        error=str(e))
            raise SchemaValidationError(f"Job validation failed: {str(e)}")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics for monitoring."""
        return {
            'valid_columns': len(self.VALID_COLUMNS),
            'required_fields': len(self.REQUIRED_FIELDS),
            'array_fields': len(self.ARRAY_FIELDS),
            'date_fields': len(self.DATE_FIELDS),
            'json_fields': len(self.JSON_FIELDS),
            'column_list': sorted(list(self.VALID_COLUMNS)),
            'required_list': sorted(list(self.REQUIRED_FIELDS))
        }
    
    def validate_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of jobs and return statistics.
        
        Args:
            jobs_data: List of job data dictionaries
            
        Returns:
            Validation statistics and results
        """
        results = {
            'total_jobs': len(jobs_data),
            'valid_jobs': [],
            'invalid_jobs': [],
            'validation_errors': []
        }
        
        for i, job_data in enumerate(jobs_data):
            job_url = job_data.get('source_url', f'job_{i}')
            
            try:
                valid_job = self.validate_complete_job(job_data, job_url)
                results['valid_jobs'].append(valid_job)
            except SchemaValidationError as e:
                results['invalid_jobs'].append({
                    'job_url': job_url,
                    'error': str(e),
                    'original_data': job_data
                })
                results['validation_errors'].append(str(e))
        
        logger.info("Batch validation completed",
                   total_jobs=results['total_jobs'],
                   valid_jobs=len(results['valid_jobs']),
                   invalid_jobs=len(results['invalid_jobs']))
        
        return results