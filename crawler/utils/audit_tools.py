#!/usr/bin/env python3
"""
OUTILS D'AUDIT - Comparaison audit vs production avec analyse d'incohérences

Ce module compare les données extraites en mode audit strict (CSS pur) 
avec les données du mode production (avec enrichissement) pour identifier
les incohérences introduites par le pipeline de transformation.

Fonctionnalités :
✅ Comparaison champ par champ audit vs production
✅ Détection automatique des incohérences
✅ Analyse des transformations problématiques
✅ Génération de rapports détaillés
✅ Recommandations d'amélioration
✅ Score de qualité des données

Usage: from crawler.utils.audit_tools import AuditComparator
"""

import json
import copy
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class InconsistencyType(Enum):
    """Types d'incohérences détectées"""
    LOGICAL_CONTRADICTION = "logical_contradiction"
    DATA_LOSS = "data_loss"
    UNWANTED_MODIFICATION = "unwanted_modification"
    FORMAT_CORRUPTION = "format_corruption"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_ENRICHMENT = "invalid_enrichment"
    CLASSIFICATION_ERROR = "classification_error"

@dataclass
class InconsistencyReport:
    """Rapport d'incohérence détaillée"""
    field_name: str
    inconsistency_type: InconsistencyType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    audit_value: Any
    production_value: Any
    recommendation: str
    confidence: float  # 0.0 - 1.0

@dataclass
class ComparisonSummary:
    """Résumé de comparaison audit vs production"""
    total_fields_compared: int
    identical_fields: int
    modified_fields: int
    enriched_fields: int
    corrupted_fields: int
    consistency_score: float
    data_quality_score: float

class AuditComparator:
    """Comparateur de données audit vs production"""
    
    def __init__(self):
        # Configuration des règles de comparaison
        self.comparison_rules = self._init_comparison_rules()
        self.field_priorities = self._init_field_priorities()
        
    def _init_comparison_rules(self) -> Dict:
        """Initialise les règles de comparaison"""
        return {
            # Champs qui ne devraient JAMAIS changer
            'immutable_fields': [
                'source_url', 'original_url', 'scraped_at', 'url'
            ],
            
            # Champs qui peuvent être enrichis mais pas modifiés
            'enrichable_only': [
                'skills', 'education_level', 'experience_level', 
                'salary', 'languages', 'contact_email', 'contact_phone'
            ],
            
            # Champs qui peuvent être normalisés
            'normalizable_fields': [
                'location', 'company_name', 'title', 'contract_type'
            ],
            
            # Champs booléens qui doivent rester cohérents
            'boolean_consistency': [
                'remote_possible', 'item_is_remote'
            ],
            
            # Formats de date acceptés
            'date_formats': [
                '%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y',
                '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'
            ],
            
            # Valeurs d'énumération valides
            'valid_enums': {
                'education_level': [
                    'Aucun diplôme', 'Bac', 'Bac+2', 'Bac+3', 
                    'Bac+4', 'Bac+5', 'Bac+5 et plus'
                ],
                'experience_level': [
                    'Débutant', 'Junior', 'Confirmé', 'Senior', 'Expert'
                ],
                'contract_type': [
                    'CDI', 'CDD', 'Stage', 'Freelance', 
                    'Consultant', 'Temps partiel', 'Intérim'
                ]
            }
        }
    
    def _init_field_priorities(self) -> Dict[str, str]:
        """Définit les priorités des champs pour l'analyse"""
        return {
            # Champs critiques pour la cohérence
            'title': 'CRITICAL',
            'company_name': 'CRITICAL',
            'location': 'CRITICAL',
            'source_url': 'CRITICAL',
            'remote_possible': 'HIGH',
            'item_is_remote': 'HIGH',
            'date_posted': 'HIGH',
            'contract_type': 'HIGH',
            
            # Champs importants mais non critiques
            'education_level': 'MEDIUM',
            'experience_level': 'MEDIUM',
            'salary': 'MEDIUM',
            'skills': 'MEDIUM',
            
            # Champs optionnels
            'contact_email': 'LOW',
            'contact_phone': 'LOW',
            'languages': 'LOW',
            'tags': 'LOW'
        }
    
    def compare_data(self, audit_data: Dict, production_data: Dict, job_url: str) -> Dict[str, Any]:
        """
        Compare les données audit vs production
        
        Args:
            audit_data: Données extraites en mode audit strict
            production_data: Données du mode production (avec enrichissement)
            job_url: URL de l'offre d'emploi
            
        Returns:
            Dict contenant l'analyse complète de comparaison
        """
        print(f"\n🔍 === COMPARAISON AUDIT vs PRODUCTION ===")
        print(f"URL: {job_url}")
        
        comparison_result = {
            'job_url': job_url,
            'comparison_timestamp': datetime.now().isoformat(),
            'audit_fields_count': len(audit_data),
            'production_fields_count': len(production_data),
            'field_analysis': {},
            'inconsistencies': [],
            'summary': None,
            'recommendations': []
        }
        
        # Analyser chaque champ
        all_fields = set(audit_data.keys()) | set(production_data.keys())
        
        for field_name in all_fields:
            if field_name.startswith('_'):  # Ignorer les métadonnées
                continue
                
            field_analysis = self._analyze_field(
                field_name,
                audit_data.get(field_name),
                production_data.get(field_name)
            )
            
            comparison_result['field_analysis'][field_name] = field_analysis
            
            # Détecter les incohérences
            inconsistencies = self._detect_field_inconsistencies(
                field_name,
                audit_data.get(field_name),
                production_data.get(field_name),
                field_analysis
            )
            
            comparison_result['inconsistencies'].extend(inconsistencies)
        
        # Détecter les incohérences logiques globales
        global_inconsistencies = self._detect_global_inconsistencies(
            audit_data, production_data
        )
        comparison_result['inconsistencies'].extend(global_inconsistencies)
        
        # Générer le résumé
        summary = self._generate_comparison_summary(comparison_result)
        comparison_result['summary'] = asdict(summary)
        
        # Générer les recommandations
        recommendations = self._generate_recommendations(comparison_result)
        comparison_result['recommendations'] = recommendations
        
        # Afficher les résultats
        self._print_comparison_results(comparison_result)
        
        return comparison_result
    
    def _analyze_field(self, field_name: str, audit_value: Any, production_value: Any) -> Dict:
        """Analyse un champ spécifique"""
        analysis = {
            'field_name': field_name,
            'audit_value': audit_value,
            'production_value': production_value,
            'status': 'unknown',
            'change_type': None,
            'priority': self.field_priorities.get(field_name, 'LOW')
        }
        
        # Cas 1: Valeurs identiques
        if audit_value == production_value:
            analysis['status'] = 'identical'
            analysis['change_type'] = 'none'
        
        # Cas 2: Enrichissement (audit vide, production remplie)
        elif not audit_value and production_value:
            analysis['status'] = 'enriched'
            analysis['change_type'] = 'enrichment'
        
        # Cas 3: Perte de données (audit rempli, production vide)
        elif audit_value and not production_value:
            analysis['status'] = 'data_loss'
            analysis['change_type'] = 'loss'
        
        # Cas 4: Modification (deux valeurs différentes non vides)
        elif audit_value and production_value and audit_value != production_value:
            analysis['status'] = 'modified'
            analysis['change_type'] = 'modification'
            
            # Analyser le type de modification
            if self._is_normalization(field_name, audit_value, production_value):
                analysis['change_type'] = 'normalization'
            elif self._is_format_change(audit_value, production_value):
                analysis['change_type'] = 'format_change'
            else:
                analysis['change_type'] = 'content_change'
        
        # Cas 5: Les deux sont vides
        else:
            analysis['status'] = 'both_empty'
            analysis['change_type'] = 'none'
        
        return analysis
    
    def _detect_field_inconsistencies(self, field_name: str, audit_value: Any, 
                                    production_value: Any, field_analysis: Dict) -> List[InconsistencyReport]:
        """Détecte les incohérences pour un champ spécifique"""
        inconsistencies = []
        
        # Règle 1: Champs immutables modifiés
        if field_name in self.comparison_rules['immutable_fields']:
            if field_analysis['status'] == 'modified':
                inconsistencies.append(InconsistencyReport(
                    field_name=field_name,
                    inconsistency_type=InconsistencyType.UNWANTED_MODIFICATION,
                    severity='CRITICAL',
                    description=f'Champ immutable modifié: {audit_value} → {production_value}',
                    audit_value=audit_value,
                    production_value=production_value,
                    recommendation='Corriger le pipeline pour préserver ce champ',
                    confidence=1.0
                ))
        
        # Règle 2: Perte de données importantes
        if field_analysis['status'] == 'data_loss' and field_analysis['priority'] in ['CRITICAL', 'HIGH']:
            inconsistencies.append(InconsistencyReport(
                field_name=field_name,
                inconsistency_type=InconsistencyType.DATA_LOSS,
                severity=field_analysis['priority'],
                description=f'Perte de données importantes: "{audit_value}" → vide',
                audit_value=audit_value,
                production_value=production_value,
                recommendation='Vérifier pourquoi ce champ est effacé pendant l\'enrichissement',
                confidence=0.9
            ))
        
        # Règle 3: Énumérations invalides
        if field_name in self.comparison_rules['valid_enums']:
            valid_values = self.comparison_rules['valid_enums'][field_name]
            if production_value and production_value not in valid_values:
                inconsistencies.append(InconsistencyReport(
                    field_name=field_name,
                    inconsistency_type=InconsistencyType.INVALID_ENRICHMENT,
                    severity='MEDIUM',
                    description=f'Valeur enrichie invalide: "{production_value}" (valeurs valides: {valid_values})',
                    audit_value=audit_value,
                    production_value=production_value,
                    recommendation=f'Normaliser vers une valeur valide ou améliorer l\'enrichissement',
                    confidence=0.8
                ))
        
        # Règle 4: Formats de date corrompus
        if field_name in ['date_posted', 'valid_through', 'deadline']:
            if production_value and not self._is_valid_date_format(production_value):
                inconsistencies.append(InconsistencyReport(
                    field_name=field_name,
                    inconsistency_type=InconsistencyType.FORMAT_CORRUPTION,
                    severity='HIGH',
                    description=f'Format de date corrompu: "{production_value}"',
                    audit_value=audit_value,
                    production_value=production_value,
                    recommendation='Corriger le parsing et la normalisation des dates',
                    confidence=0.9
                ))
        
        return inconsistencies
    
    def _detect_global_inconsistencies(self, audit_data: Dict, production_data: Dict) -> List[InconsistencyReport]:
        """Détecte les incohérences logiques globales"""
        inconsistencies = []
        
        # Incohérence remote_possible vs item_is_remote
        rp_audit = audit_data.get('remote_possible')
        rp_prod = production_data.get('remote_possible')
        iir_audit = audit_data.get('item_is_remote')
        iir_prod = production_data.get('item_is_remote')
        
        # Convertir en booléens
        rp_prod_bool = self._to_boolean(rp_prod)
        iir_prod_bool = self._to_boolean(iir_prod)
        
        if (rp_prod_bool is not None and iir_prod_bool is not None and 
            rp_prod_bool != iir_prod_bool):
            inconsistencies.append(InconsistencyReport(
                field_name='remote_work_consistency',
                inconsistency_type=InconsistencyType.LOGICAL_CONTRADICTION,
                severity='HIGH',
                description=f'Contradiction: remote_possible={rp_prod} mais item_is_remote={iir_prod}',
                audit_value={'remote_possible': rp_audit, 'item_is_remote': iir_audit},
                production_value={'remote_possible': rp_prod, 'item_is_remote': iir_prod},
                recommendation='Unifier la logique de détection du travail à distance',
                confidence=0.95
            ))
        
        return inconsistencies
    
    def _generate_comparison_summary(self, comparison_result: Dict) -> ComparisonSummary:
        """Génère un résumé de la comparaison"""
        field_analysis = comparison_result['field_analysis']
        
        total_fields = len(field_analysis)
        identical = sum(1 for f in field_analysis.values() if f['status'] == 'identical')
        modified = sum(1 for f in field_analysis.values() if f['status'] == 'modified')
        enriched = sum(1 for f in field_analysis.values() if f['status'] == 'enriched')
        corrupted = sum(1 for f in field_analysis.values() if f['status'] == 'data_loss')
        
        # Calculer les scores
        consistency_score = (identical / total_fields * 100) if total_fields > 0 else 0
        
        # Score de qualité basé sur les incohérences
        inconsistencies = comparison_result['inconsistencies']
        critical_count = sum(1 for inc in inconsistencies if inc.severity == 'CRITICAL')
        high_count = sum(1 for inc in inconsistencies if inc.severity == 'HIGH')
        medium_count = sum(1 for inc in inconsistencies if inc.severity == 'MEDIUM')
        
        quality_penalty = (critical_count * 20) + (high_count * 10) + (medium_count * 5)
        data_quality_score = max(0, 100 - quality_penalty)
        
        return ComparisonSummary(
            total_fields_compared=total_fields,
            identical_fields=identical,
            modified_fields=modified,
            enriched_fields=enriched,
            corrupted_fields=corrupted,
            consistency_score=round(consistency_score, 2),
            data_quality_score=round(data_quality_score, 2)
        )
    
    def _generate_recommendations(self, comparison_result: Dict) -> List[str]:
        """Génère des recommandations d'amélioration"""
        recommendations = []
        inconsistencies = comparison_result['inconsistencies']
        
        # Analyser les types d'incohérences
        critical_count = sum(1 for inc in inconsistencies if inc.severity == 'CRITICAL')
        high_count = sum(1 for inc in inconsistencies if inc.severity == 'HIGH')
        
        if critical_count > 0:
            recommendations.append(
                f"🚨 CRITIQUE: {critical_count} incohérences critiques détectées. "
                "Arrêter le pipeline de production jusqu'à correction."
            )
        
        if high_count > 0:
            recommendations.append(
                f"⚠️ URGENT: {high_count} incohérences importantes détectées. "
                "Réviser le processus d'enrichissement."
            )
        
        # Recommandations spécifiques par type
        inconsistency_types = [inc.inconsistency_type for inc in inconsistencies]
        
        if InconsistencyType.LOGICAL_CONTRADICTION in inconsistency_types:
            recommendations.append(
                "🔧 Unifier la logique de détection des champs booléens (remote_work, etc.)"
            )
        
        if InconsistencyType.DATA_LOSS in inconsistency_types:
            recommendations.append(
                "📊 Réviser l'ordre des transformations pour éviter la perte de données"
            )
        
        if InconsistencyType.UNWANTED_MODIFICATION in inconsistency_types:
            recommendations.append(
                "🔒 Protéger les champs immutables contre les modifications"
            )
        
        if InconsistencyType.INVALID_ENRICHMENT in inconsistency_types:
            recommendations.append(
                "🤖 Améliorer la validation des données enrichies par LLM"
            )
        
        # Recommandations générales
        summary = comparison_result['summary']
        if summary['consistency_score'] < 80:
            recommendations.append(
                "📈 Score de cohérence faible. Réviser l'ensemble du pipeline."
            )
        
        if summary['data_quality_score'] < 70:
            recommendations.append(
                "🎯 Score de qualité faible. Implémenter plus de validations."
            )
        
        return recommendations
    
    def _is_normalization(self, field_name: str, audit_value: Any, production_value: Any) -> bool:
        """Détermine si une modification est une normalisation acceptable"""
        if field_name not in self.comparison_rules['normalizable_fields']:
            return False
        
        # Exemples de normalisation acceptable
        if isinstance(audit_value, str) and isinstance(production_value, str):
            # Normalisation de casse
            if audit_value.lower().strip() == production_value.lower().strip():
                return True
            
            # Normalisation d'espaces
            if ' '.join(audit_value.split()) == ' '.join(production_value.split()):
                return True
        
        return False
    
    def _is_format_change(self, audit_value: Any, production_value: Any) -> bool:
        """Détermine si c'est juste un changement de format"""
        if type(audit_value) != type(production_value):
            return True
        
        # Changements de format de date
        if isinstance(audit_value, str) and isinstance(production_value, str):
            if self._is_valid_date_format(audit_value) and self._is_valid_date_format(production_value):
                return True
        
        return False
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Vérifie si une chaîne a un format de date valide"""
        if not isinstance(date_str, str):
            return False
        
        from datetime import datetime
        
        for fmt in self.comparison_rules['date_formats']:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _to_boolean(self, value) -> Optional[bool]:
        """Convertit une valeur en booléen"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_val = value.lower().strip()
            if lower_val in ['true', '1', 'oui', 'yes', 'vrai']:
                return True
            elif lower_val in ['false', '0', 'non', 'no', 'faux']:
                return False
        return None
    
    def _print_comparison_results(self, comparison_result: Dict):
        """Affiche les résultats de comparaison"""
        summary = comparison_result['summary']
        inconsistencies = comparison_result['inconsistencies']
        
        print(f"\n📊 RÉSULTATS COMPARAISON:")
        print(f"   📋 Champs comparés: {summary['total_fields_compared']}")
        print(f"   ✅ Identiques: {summary['identical_fields']}")
        print(f"   🔄 Modifiés: {summary['modified_fields']}")
        print(f"   ➕ Enrichis: {summary['enriched_fields']}")
        print(f"   ❌ Corrompus: {summary['corrupted_fields']}")
        print(f"   📈 Score cohérence: {summary['consistency_score']}%")
        print(f"   🎯 Score qualité: {summary['data_quality_score']}%")
        
        if inconsistencies:
            print(f"\n⚠️  INCOHÉRENCES DÉTECTÉES ({len(inconsistencies)}):")
            for inc in inconsistencies[:5]:  # Afficher les 5 premières
                print(f"   {inc.severity}: {inc.field_name} - {inc.description}")
            if len(inconsistencies) > 5:
                print(f"   ... et {len(inconsistencies) - 5} autres")
    
    def export_comparison_report(self, comparison_result: Dict, filename: str = None) -> str:
        """Exporte le rapport de comparaison"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"audit_comparison_{timestamp}.json"
        
        try:
            # Convertir les InconsistencyReport en dict pour la sérialisation
            comparison_result_copy = copy.deepcopy(comparison_result)
            comparison_result_copy['inconsistencies'] = [
                asdict(inc) if hasattr(inc, '__dict__') else inc
                for inc in comparison_result['inconsistencies']
            ]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comparison_result_copy, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📄 Rapport exporté: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Erreur export: {e}")
            return None

# Fonction utilitaire pour comparaison rapide
def quick_compare(audit_data: Dict, production_data: Dict, job_url: str) -> Dict:
    """Comparaison rapide audit vs production"""
    comparator = AuditComparator()
    return comparator.compare_data(audit_data, production_data, job_url)