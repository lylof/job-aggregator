# Design Document

## Overview

Ce document décrit la solution complète pour corriger le problème de mapping des champs entre les données générées par l'IA et le schéma de la base de données Supabase, tout en implémentant une architecture multi-sources universelle qui préserve toutes les données spécifiques à chaque source.

**Problème principal** : L'IA génère un champ `profile` alors que la base attend `profile_description`.

**Solution étendue** : Architecture universelle qui gère les 6 sources existantes (emploi_tg, linkedin_togo, indeed_togo, anpetogo, emploitogo_info, yop_lfrii) sans perte de données.

## Architecture

### Current Flow (Problematic)
```
AI Structuring → Raw Job Data → DatabaseService.upsert_job() → Supabase
                                      ↑
                                 ERREUR: champ 'profile' inexistant
```

### Proposed Flow (Solution)
```
AI Structuring → Raw Job Data → FieldMapper.map_fields() → DatabaseService.upsert_job() → Supabase
                                      ↑
                                 Mapping automatique des champs
```

## Components and Interfaces

### 1. FieldMapper Class

**Location**: `services/field_mapper.py`

```python
class FieldMapper:
    """Maps AI-generated fields to database schema fields."""
    
    FIELD_MAPPINGS = {
        'profile': 'profile_description',
        'job_description': 'description',
        'company_name': 'company',
        'job_title': 'title',
        # Autres mappings si nécessaires
    }
    
    def map_job_fields(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map AI fields to database fields."""
        
    def validate_schema_compatibility(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean fields against database schema."""
```

### 2. Enhanced DatabaseService

**Modification**: `services/database_service.py`

```python
class DatabaseService:
    def __init__(self):
        # Existing code...
        self.field_mapper = FieldMapper()
    
    def _prepare_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced preparation with field mapping."""
        # 1. Apply field mapping
        mapped_data = self.field_mapper.map_job_fields(job_data)
        
        # 2. Validate schema compatibility
        validated_data = self.field_mapper.validate_schema_compatibility(mapped_data)
        
        # 3. Existing preparation logic
        # ...
```

### 3. Schema Validator

**Location**: `utils/schema_validator.py`

```python
class SchemaValidator:
    """Validates data against Supabase schema."""
    
    VALID_COLUMNS = {
        'id', 'item_id', 'title', 'company', 'source_url', 'source_site',
        'description', 'location', 'salary_range', 'contract_type',
        'experience_level', 'education_level', 'sector', 'missions',
        'required_skills', 'profile_description', 'posted_date',
        'application_deadline', 'contact_email', 'contact_phone',
        'extraction_method', 'extraction_metadata', 'quality_score',
        'raw_data', 'created_at', 'updated_at', 'is_active'
    }
    
    def filter_valid_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove invalid fields and log warnings."""
```

## Data Models

### Universal Schema Architecture

```python
# SCHÉMA UNIVERSEL (colonnes fixes Supabase)
UNIVERSAL_SCHEMA = {
    # Champs essentiels (toutes sources)
    "title": "Titre du poste",
    "company": "Nom entreprise", 
    "location": "Localisation",
    "description": "Description",
    "source_url": "URL source",
    "source_site": "Site source",
    
    # Champs communs (la plupart des sources)
    "contract_type": "Type contrat",
    "salary_range": "Salaire",
    "experience_level": "Expérience",
    "education_level": "Formation",
    "sector": "Secteur",
    "missions": ["Missions"],
    "required_skills": ["Compétences"],
    "profile_description": "Profil recherché",  # ← CORRECTION CRITIQUE
    "posted_date": "Date publication",
    "application_deadline": "Date limite",
    "contact_email": "Email contact",
    "contact_phone": "Téléphone contact",
    
    # Métadonnées flexibles (JSONB)
    "extraction_metadata": {
        "source_specific_data": {
            # Données spécifiques par source
        }
    },
    "raw_data": {
        # Backup complet des données originales
    }
}
```

### Multi-Source Field Mapping

```python
FIELD_MAPPINGS = {
    # Corrections universelles
    'profile': 'profile_description',
    'job_description': 'description',
    'company_name': 'company',
    'job_title': 'title',
    
    # Mappings spécifiques par source
    'source_mappings': {
        'emploi_tg': {
            'company_logo': 'extraction_metadata.source_specific_data.emploi_tg_data.company_logo',
            'number_of_positions': 'extraction_metadata.source_specific_data.emploi_tg_data.number_of_positions',
            'languages_required': 'extraction_metadata.source_specific_data.emploi_tg_data.languages_required'
        },
        'linkedin_togo': {
            'company_logo': 'extraction_metadata.source_specific_data.linkedin_data.company_logo',
            'company_size': 'extraction_metadata.source_specific_data.linkedin_data.company_size',
            'applicants_count': 'extraction_metadata.source_specific_data.linkedin_data.applicants_count'
        },
        'indeed_togo': {
            'salary_estimate': 'extraction_metadata.source_specific_data.indeed_data.salary_estimate',
            'company_rating': 'extraction_metadata.source_specific_data.indeed_data.company_rating'
        }
    }
}
```

### Validation Rules

```python
VALIDATION_RULES = {
    'required_fields': ['title', 'company', 'source_url', 'extraction_method'],
    'optional_fields': ['description', 'location', 'salary_range', 'profile_description'],
    'array_fields': ['missions', 'required_skills'],
    'date_fields': ['posted_date', 'application_deadline'],
    'json_fields': ['extraction_metadata', 'raw_data']
}
```

## Error Handling

### 1. Field Mapping Errors

```python
class FieldMappingError(Exception):
    """Raised when field mapping fails."""
    pass

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass
```

### 2. Graceful Degradation

- Si un champ ne peut pas être mappé → Log warning et continue
- Si un champ est invalide → Supprime le champ et continue
- Si tous les champs requis sont présents → Sauvegarde réussie
- Si des champs requis manquent → Log error mais continue avec les autres jobs

### 3. Logging Strategy

```python
logger.warning("Field mapping applied", 
               original_field="profile", 
               mapped_field="profile_description",
               job_url=job_data.get('source_url'))

logger.error("Invalid field removed", 
             field_name="unknown_field",
             job_url=job_data.get('source_url'))
```

## Testing Strategy

### 1. Unit Tests

- `test_field_mapper.py`: Test tous les mappings de champs
- `test_schema_validator.py`: Test validation du schéma
- `test_database_service_enhanced.py`: Test intégration complète

### 2. Integration Tests

- Test avec données réelles d'IA (incluant champ `profile`)
- Test avec schéma Supabase réel
- Test de performance avec batch de 25 jobs

### 3. Regression Tests

- Vérifier que les jobs existants continuent de fonctionner
- Vérifier que les nouveaux champs IA sont gérés
- Vérifier que les statistiques sont correctes

## Implementation Plan

### Phase 1: Core Mapping
1. Créer `FieldMapper` avec mappings de base
2. Intégrer dans `DatabaseService._prepare_job_data()`
3. Tester avec le champ `profile` → `profile_description`

### Phase 2: Schema Validation
1. Créer `SchemaValidator` avec colonnes valides
2. Intégrer validation dans le pipeline
3. Ajouter logging détaillé

### Phase 3: Error Handling
1. Ajouter gestion d'erreurs gracieuse
2. Améliorer les logs d'audit
3. Tester avec cas d'erreur

### Phase 4: Testing & Validation
1. Tests unitaires complets
2. Test d'intégration avec Supabase
3. Validation avec cycle complet de 25 jobs

## Performance Considerations

- **Mapping Overhead**: Négligeable (simple dictionnaire lookup)
- **Validation Cost**: Minimal (set membership check)
- **Memory Impact**: Aucun (transformation in-place)
- **Latency**: <1ms par job pour mapping + validation

## Security Considerations

- **Field Sanitization**: Validation des noms de champs contre injection
- **Data Integrity**: Préservation des données critiques
- **Audit Trail**: Logging de toutes les transformations
- **Schema Protection**: Validation stricte contre le schéma autorisé