"""
Validateur pour le schéma JSON standard emploi.tg
"""

import json
from typing import Dict, Any, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class EmploiTgValidator:
    """
    Validateur pour s'assurer que les données extraites respectent
    le schéma JSON standard emploi.tg.
    """
    
    # Champs obligatoires par section
    REQUIRED_FIELDS = {
        "metadata": ["source_site", "extraction_method"],
        "job_summary": ["title", "location"],
        "company": ["name"],
        "job_details": ["position_title"],
        "job_criteria": ["contract_type", "region"]
    }
    
    # Champs optionnels fréquents (pour les statistiques)
    FREQUENT_OPTIONAL_FIELDS = {
        "job_details.benefits": 0.75,  # Présent dans 75% des offres
        "required_profile.experience": 0.75,
        "job_criteria.required_languages": 0.50,
        "company.website": 0.60,
        "skills_keywords": 0.80
    }
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
        self.validation_stats = {}
    
    def validate(self, data: Dict[str, Any], source_url: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Valide les données extraites selon le schéma emploi.tg.
        
        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        logger.info("Validating emploi.tg data structure", url=source_url)
        
        # Validation de la structure générale
        self._validate_structure(data)
        
        # Validation des champs obligatoires
        self._validate_required_fields(data)
        
        # Validation de la cohérence des données
        self._validate_data_consistency(data)
        
        # Validation des types de données
        self._validate_data_types(data)
        
        # Validation des URLs
        self._validate_urls(data)
        
        # Génération des avertissements pour les champs manquants fréquents
        self._check_frequent_optional_fields(data)
        
        is_valid = len(self.validation_errors) == 0
        
        logger.info("Validation completed", 
                   is_valid=is_valid, 
                   errors_count=len(self.validation_errors),
                   warnings_count=len(self.validation_warnings))
        
        return is_valid, self.validation_errors, self.validation_warnings
    
    def _validate_structure(self, data: Dict[str, Any]):
        """Valide la structure générale du JSON."""
        expected_sections = [
            "metadata", "job_summary", "company", "job_details", 
            "required_profile", "job_criteria", "skills_keywords", "application"
        ]
        
        for section in expected_sections:
            if section not in data:
                self.validation_errors.append(f"Section manquante: {section}")
    
    def _validate_required_fields(self, data: Dict[str, Any]):
        """Valide la présence des champs obligatoires."""
        for section, required_fields in self.REQUIRED_FIELDS.items():
            if section not in data:
                continue
                
            section_data = data[section]
            if not isinstance(section_data, dict):
                self.validation_errors.append(f"Section {section} doit être un objet")
                continue
            
            for field in required_fields:
                if field not in section_data or section_data[field] is None or section_data[field] == "":
                    self.validation_errors.append(f"Champ obligatoire manquant: {section}.{field}")
    
    def _validate_data_consistency(self, data: Dict[str, Any]):
        """Valide la cohérence entre les différentes sections."""
        try:
            # Cohérence des titres
            job_summary_title = data.get("job_summary", {}).get("title")
            job_details_title = data.get("job_details", {}).get("position_title")
            
            if job_summary_title and job_details_title:
                if job_summary_title.strip() != job_details_title.strip():
                    self.validation_warnings.append(
                        f"Incohérence des titres: '{job_summary_title}' vs '{job_details_title}'"
                    )
            
            # Cohérence de la localisation
            summary_location = data.get("job_summary", {}).get("location")
            criteria_region = data.get("job_criteria", {}).get("region")
            criteria_city = data.get("job_criteria", {}).get("city")
            
            if summary_location and criteria_city:
                if summary_location.strip() != criteria_city.strip():
                    self.validation_warnings.append(
                        f"Incohérence de localisation: '{summary_location}' vs '{criteria_city}'"
                    )
            
            # Cohérence du nom d'entreprise
            company_name = data.get("company", {}).get("name")
            if company_name:
                # Vérifier que le nom d'entreprise n'est pas un placeholder
                if company_name.lower() in ["non extrait", "n/a", "inconnu"]:
                    self.validation_errors.append("Nom d'entreprise non extrait correctement")
        
        except Exception as e:
            self.validation_warnings.append(f"Erreur lors de la validation de cohérence: {str(e)}")
    
    def _validate_data_types(self, data: Dict[str, Any]):
        """Valide les types de données."""
        # Validation des listes
        list_fields = [
            "job_summary.sectors",
            "job_summary.experience_levels", 
            "job_summary.education_levels",
            "job_summary.contract_types",
            "company.activity_sectors",
            "job_details.responsibilities",
            "job_details.benefits",
            "required_profile.qualifications",
            "required_profile.education_training",
            "required_profile.technical_skills",
            "required_profile.soft_skills",
            "job_criteria.sectors",
            "job_criteria.activity_sectors",
            "job_criteria.experience_level",
            "job_criteria.education_level",
            "job_criteria.required_languages",
            "skills_keywords",
            "application.application_urls"
        ]
        
        for field_path in list_fields:
            value = self._get_nested_value(data, field_path)
            if value is not None and not isinstance(value, list):
                self.validation_errors.append(f"Le champ {field_path} doit être une liste")
        
        # Validation des entiers
        int_fields = ["job_criteria.positions_available"]
        for field_path in int_fields:
            value = self._get_nested_value(data, field_path)
            if value is not None and not isinstance(value, (int, type(None))):
                try:
                    int(value)
                except (ValueError, TypeError):
                    self.validation_warnings.append(f"Le champ {field_path} devrait être un entier")
    
    def _validate_urls(self, data: Dict[str, Any]):
        """Valide les URLs présentes dans les données."""
        url_fields = [
            "company.profile_url",
            "company.website", 
            "company.job_listings_url",
            "company.logo_url"
        ]
        
        for field_path in url_fields:
            url = self._get_nested_value(data, field_path)
            if url and isinstance(url, str):
                if not (url.startswith("http://") or url.startswith("https://")):
                    self.validation_warnings.append(f"URL potentiellement invalide: {field_path} = {url}")
        
        # Validation des URLs de candidature
        app_urls = data.get("application", {}).get("application_urls", [])
        if isinstance(app_urls, list):
            for i, url in enumerate(app_urls):
                if url and not (url.startswith("http://") or url.startswith("https://")):
                    self.validation_warnings.append(f"URL de candidature invalide [{i}]: {url}")
    
    def _check_frequent_optional_fields(self, data: Dict[str, Any]):
        """Vérifie la présence des champs optionnels fréquents."""
        for field_path, frequency in self.FREQUENT_OPTIONAL_FIELDS.items():
            value = self._get_nested_value(data, field_path)
            if value is None or (isinstance(value, list) and len(value) == 0):
                self.validation_warnings.append(
                    f"Champ fréquent manquant ({frequency*100:.0f}% des offres): {field_path}"
                )
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Récupère une valeur dans un dictionnaire imbriqué."""
        keys = field_path.split(".")
        value = data
        
        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except (KeyError, TypeError):
            return None
    
    def generate_validation_report(self, data: Dict[str, Any], source_url: str = None) -> str:
        """Génère un rapport de validation détaillé."""
        is_valid, errors, warnings = self.validate(data, source_url)
        
        report = []
        report.append("=" * 60)
        report.append("📋 RAPPORT DE VALIDATION EMPLOI.TG")
        report.append("=" * 60)
        
        if source_url:
            report.append(f"🔗 URL: {source_url}")
        
        report.append(f"✅ Statut: {'VALIDE' if is_valid else 'INVALIDE'}")
        report.append(f"❌ Erreurs: {len(errors)}")
        report.append(f"⚠️  Avertissements: {len(warnings)}")
        
        if errors:
            report.append("\\n🚨 ERREURS:")
            for i, error in enumerate(errors, 1):
                report.append(f"  {i}. {error}")
        
        if warnings:
            report.append("\\n⚠️  AVERTISSEMENTS:")
            for i, warning in enumerate(warnings, 1):
                report.append(f"  {i}. {warning}")
        
        # Statistiques de complétude
        report.append("\\n📊 STATISTIQUES DE COMPLÉTUDE:")
        total_sections = len(["metadata", "job_summary", "company", "job_details", 
                             "required_profile", "job_criteria", "skills_keywords", "application"])
        present_sections = len([s for s in ["metadata", "job_summary", "company", "job_details", 
                                           "required_profile", "job_criteria", "skills_keywords", "application"] 
                               if s in data and data[s]])
        
        completeness = (present_sections / total_sections) * 100
        report.append(f"  📋 Sections présentes: {present_sections}/{total_sections} ({completeness:.1f}%)")
        
        # Champs obligatoires
        total_required = sum(len(fields) for fields in self.REQUIRED_FIELDS.values())
        missing_required = len([e for e in errors if "obligatoire manquant" in e])
        present_required = total_required - missing_required
        
        report.append(f"  🔑 Champs obligatoires: {present_required}/{total_required} ({(present_required/total_required)*100:.1f}%)")
        
        report.append("=" * 60)
        
        return "\\n".join(report)