"""Field Mapper Service for JinaScraper - Universal Multi-Source Architecture."""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class FieldMappingError(Exception):
    """Raised when field mapping fails."""
    pass


class FieldMapper:
    """Maps AI-generated fields to database schema fields with multi-source support."""
    
    # CORRECTION CRITIQUE : profile → profile_description
    UNIVERSAL_FIELD_MAPPINGS = {
        # Corrections universelles critiques
        'profile': 'profile_description',  # ← CORRECTION PRINCIPALE
        'job_description': 'description',
        'company_name': 'company',
        'job_title': 'title',
        'job_location': 'location',
        'salary_info': 'salary_range',
        'job_requirements': 'required_skills',
        'job_missions': 'missions',
        'contact_info': 'contact_email',
        'phone_number': 'contact_phone',
        'employment_type': 'contract_type',
        'experience_required': 'experience_level',
        'education_required': 'education_level',
        'industry_sector': 'sector',
        'publication_date': 'posted_date',
        'deadline_date': 'application_deadline'
    }
    
    # Champs universels (colonnes fixes Supabase)
    UNIVERSAL_FIELDS = {
        'id', 'item_id', 'title', 'company', 'source_url', 'source_site',
        'description', 'location', 'salary_range', 'contract_type',
        'experience_level', 'education_level', 'sector', 'missions',
        'required_skills', 'profile_description', 'posted_date',
        'application_deadline', 'contact_email', 'contact_phone',
        'extraction_method', 'extraction_metadata', 'quality_score',
        'raw_data', 'created_at', 'updated_at', 'is_active'
    }
    
    # Mappings spécifiques par source (pour extraction_metadata)
    SOURCE_SPECIFIC_MAPPINGS = {
        'emploi_tg': {
            'company_logo': 'company_logo',
            'company_website': 'company_website',
            'number_of_positions': 'number_of_positions',
            'languages_required': 'languages_required',
            'benefits': 'benefits'
        },
        'linkedin_togo': {
            'company_logo': 'company_logo',
            'company_size': 'company_size',
            'applicants_count': 'applicants_count',
            'job_level': 'job_level',
            'industry': 'industry',
            'company_rating': 'company_rating'
        },
        'indeed_togo': {
            'salary_estimate': 'salary_estimate',
            'company_rating': 'company_rating',
            'company_reviews': 'company_reviews',
            'job_type': 'job_type',
            'benefits': 'benefits'
        },
        'anpetogo': {
            'reference_number': 'reference_number',
            'publication_date': 'publication_date',
            'application_method': 'application_method',
            'contact_person': 'contact_person'
        },
        'emploitogo_info': {
            'job_category': 'job_category',
            'posting_date': 'posting_date',
            'application_deadline': 'application_deadline',
            'contact_email': 'contact_email'
        },
        'yop_lfrii': {
            'organization_type': 'organization_type',
            'project_duration': 'project_duration',
            'funding_source': 'funding_source',
            'application_procedure': 'application_procedure'
        }
    }
    
    def __init__(self):
        """Initialize the FieldMapper."""
        logger.info("FieldMapper initialized", 
                   universal_mappings=len(self.UNIVERSAL_FIELD_MAPPINGS),
                   sources_supported=len(self.SOURCE_SPECIFIC_MAPPINGS))
    
    def map_job_fields(self, job_data: Dict[str, Any], source_name: str = None) -> Dict[str, Any]:
        """
        Map AI fields to database fields with multi-source support.
        
        Args:
            job_data: Raw job data from AI extraction
            source_name: Source name for specific mappings
            
        Returns:
            Mapped job data with universal fields + source-specific metadata
        """
        try:
            logger.debug("Starting field mapping", 
                        source=source_name,
                        original_fields=list(job_data.keys()))
            
            # 1. Apply universal field mappings
            mapped_data = self._apply_universal_mappings(job_data.copy())
            
            # 1.5. Ensure source_site is set (CRITICAL FIX)
            if source_name and 'source_site' not in mapped_data:
                mapped_data['source_site'] = source_name
            
            # 2. Extract source-specific data
            if source_name:
                source_specific_data = self._extract_source_specific_data(
                    job_data, source_name
                )
                if source_specific_data:
                    mapped_data['extraction_metadata'] = {
                        'source_specific_data': {
                            f'{source_name}_data': source_specific_data
                        }
                    }
            
            # 3. Preserve raw data for backup
            mapped_data['raw_data'] = job_data.copy()
            
            logger.info("Field mapping completed successfully",
                       source=source_name,
                       universal_fields_mapped=len([k for k in mapped_data.keys() 
                                                   if k in self.UNIVERSAL_FIELDS]),
                       source_specific_fields=len(source_specific_data) if source_name else 0)
            
            return mapped_data
            
        except Exception as e:
            logger.error("Field mapping failed", 
                        source=source_name,
                        error=str(e),
                        original_fields=list(job_data.keys()))
            raise FieldMappingError(f"Failed to map fields for source {source_name}: {str(e)}")
    
    def _apply_universal_mappings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply universal field mappings."""
        mapped_data = {}
        
        for original_field, value in data.items():
            # Check if field needs mapping
            if original_field in self.UNIVERSAL_FIELD_MAPPINGS:
                mapped_field = self.UNIVERSAL_FIELD_MAPPINGS[original_field]
                mapped_data[mapped_field] = value
                
                logger.debug("Field mapped", 
                           original=original_field,
                           mapped=mapped_field,
                           value_type=type(value).__name__)
            else:
                # Keep field as-is if it's a universal field
                if original_field in self.UNIVERSAL_FIELDS:
                    mapped_data[original_field] = value
        
        return mapped_data
    
    def _extract_source_specific_data(self, data: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Extract source-specific data for metadata."""
        if source_name not in self.SOURCE_SPECIFIC_MAPPINGS:
            logger.warning("No specific mappings for source", source=source_name)
            return {}
        
        source_mappings = self.SOURCE_SPECIFIC_MAPPINGS[source_name]
        source_data = {}
        
        for original_field, mapped_field in source_mappings.items():
            if original_field in data:
                source_data[mapped_field] = data[original_field]
                logger.debug("Source-specific field extracted",
                           source=source_name,
                           original=original_field,
                           mapped=mapped_field)
        
        return source_data
    
    def validate_schema_compatibility(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean fields against database schema.
        
        Args:
            job_data: Job data to validate
            
        Returns:
            Cleaned job data with only valid fields
        """
        try:
            validated_data = {}
            invalid_fields = []
            
            for field, value in job_data.items():
                if field in self.UNIVERSAL_FIELDS:
                    validated_data[field] = value
                else:
                    invalid_fields.append(field)
            
            if invalid_fields:
                logger.warning("Invalid fields removed during validation",
                             invalid_fields=invalid_fields,
                             valid_fields=len(validated_data))
            
            logger.info("Schema validation completed",
                       valid_fields=len(validated_data),
                       invalid_fields=len(invalid_fields))
            
            return validated_data
            
        except Exception as e:
            logger.error("Schema validation failed", error=str(e))
            raise FieldMappingError(f"Schema validation failed: {str(e)}")
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """Get mapping statistics for monitoring."""
        return {
            'universal_mappings': len(self.UNIVERSAL_FIELD_MAPPINGS),
            'universal_fields': len(self.UNIVERSAL_FIELDS),
            'sources_supported': len(self.SOURCE_SPECIFIC_MAPPINGS),
            'source_names': list(self.SOURCE_SPECIFIC_MAPPINGS.keys()),
            'critical_mappings': {
                'profile_to_profile_description': 'profile' in self.UNIVERSAL_FIELD_MAPPINGS
            }
        }