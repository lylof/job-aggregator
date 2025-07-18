#!/usr/bin/env python3
"""
PIPELINE CENTRALISÉ - Extraction, Validation, Enrichissement

Ce module définit le pipeline principal du crawler :
1. Extraction CSS pure
2. Validation stricte (champs requis, cohérence logique, formats)
3. Protection des champs immutables
4. Enrichissement optionnel (LLM, classification, etc.)
5. Validation finale avant sauvegarde

Chaque étape est traçable et testable indépendamment.
"""

from typing import Dict, Any, Optional
import copy
import logging

IMMUTABLE_FIELDS = [
    'source_url', 'original_url', 'job_id', 'extraction_date', 'source_site'
]
REQUIRED_FIELDS = ['title', 'company_name', 'location']

logger = logging.getLogger("pipeline")

class Pipeline:
    def __init__(self):
        pass

    def extract_and_validate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1 : Extraction CSS pure + validation stricte
        """
        logger.info("[PIPELINE] Extraction CSS pure et validation...")
        data = copy.deepcopy(raw_data)
        errors = []
        # Validation des champs requis
        for field in REQUIRED_FIELDS:
            if not data.get(field):
                errors.append(f"Champ requis manquant: {field}")
        # Validation logique remote
        if 'remote_possible' in data and 'item_is_remote' in data:
            if self._to_bool(data['remote_possible']) != self._to_bool(data['item_is_remote']):
                errors.append("Incohérence remote_possible vs item_is_remote")
        # Validation format date
        if 'date_posted' in data and not self._is_valid_date(data['date_posted']):
            errors.append(f"Format de date invalide: {data['date_posted']}")
        if errors:
            logger.warning(f"[PIPELINE] Erreurs de validation: {errors}")
        data['__validation_errors__'] = errors
        return data

    def protect_immutable_fields(self, original: Dict[str, Any], enriched: Dict[str, Any]) -> Dict[str, Any]:
        """
        Protège les champs immutables contre modification
        """
        for field in IMMUTABLE_FIELDS:
            if field in original:
                enriched[field] = original[field]
        return enriched

    def enrich(self, data: Dict[str, Any], enrichment_func=None) -> Dict[str, Any]:
        """
        Phase 2 : Enrichissement optionnel (LLM, classification, etc.)
        """
        logger.info("[PIPELINE] Enrichissement des données...")
        enriched = copy.deepcopy(data)
        if enrichment_func:
            enriched = enrichment_func(enriched)
        return enriched

    def validate_final(self, data: Dict[str, Any]) -> bool:
        """
        Validation finale stricte avant sauvegarde
        """
        errors = []
        for field in REQUIRED_FIELDS:
            if not data.get(field):
                errors.append(f"Champ requis manquant: {field}")
        if 'remote_possible' in data and 'item_is_remote' in data:
            if self._to_bool(data['remote_possible']) != self._to_bool(data['item_is_remote']):
                errors.append("Incohérence remote_possible vs item_is_remote")
        if 'date_posted' in data and not self._is_valid_date(data['date_posted']):
            errors.append(f"Format de date invalide: {data['date_posted']}")
        data['__validation_errors__'] = errors
        return len(errors) == 0

    def _to_bool(self, value) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.lower().strip()
            if v in ['true', '1', 'oui', 'yes', 'vrai']:
                return True
            if v in ['false', '0', 'non', 'no', 'faux']:
                return False
        return None

    def _is_valid_date(self, date_str: str) -> bool:
        # Accepte YYYY-MM-DD ou DD.MM.YYYY
        import re
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return True
        if re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
            return True
        return False 