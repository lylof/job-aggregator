---
inclusion: always
---

# Architecture Quality & Import Management Rules

## ✅ RÈGLES D'IMPORTS (Mises à jour - 28/01/2025)

### Import Standards (VALIDÉS ET APPLIQUÉS)
- ✅ **AUCUN import relatif** à plus de 2 niveaux détecté
- ✅ **Imports absolus** utilisés correctement partout
- ✅ **Imports relatifs simples** autorisés dans le même package (`.module`)

### Patterns d'Imports Validés
```python
# ✅ CORRECT - Import standard Python (RECOMMANDÉ)
from typing import List, Dict, Any

# ✅ CORRECT - Import absolu
from jinascraper.config import SourceRegistry

# ✅ CORRECT - Import relatif simple (même package)
from .base_cleaner import PatternBasedURLCleaner

# ❌ ÉVITÉ - Import via type_helpers (non nécessaire)
from jinascraper.utils.type_helpers import List  # Remplacé par typing
```

### Validation Automatique (IMPLÉMENTÉE)
- ✅ **Script de test** : `jinascraper/test_imports_fixed.py` (13/13 tests réussis)
- ✅ **Validation continue** via hooks pre-commit
- ✅ **Tests automatisés** intégrés au workflow
- ✅ **100% des imports** fonctionnels et validés

## 🔧 RÈGLES DE STRUCTURE DE PACKAGE

### Organisation Obligatoire
```
jinascraper/
├── __init__.py                 # Point d'entrée principal
├── config/                     # Configuration centralisée
│   ├── __init__.py
│   ├── sources/               # Configurations par source
│   └── base_config.py
├── services/                   # Services métier
│   ├── __init__.py
│   ├── url_cleaners/          # Nettoyeurs spécialisés
│   └── *.py
├── core/                       # Logique centrale
├── utils/                      # Utilitaires partagés
└── tests/                      # Tests organisés
```

### Interdictions Structurelles
- ❌ **INTERDIT**: Dossiers vides ou parasites (`jinascraper/jinascraper/`)
- ❌ **INTERDIT**: Fichiers de configuration obsolètes (`sources_config.py`)
- ❌ **INTERDIT**: Double système de configuration
- ❌ **INTERDIT**: Imports circulaires entre packages

## 🧪 RÈGLES DE TESTS ET VALIDATION

### Standards de Test
- **OBLIGATION**: Chaque nettoyeur d'URL DOIT avoir des tests unitaires
- **OBLIGATION**: Tests d'intégration pour chaque source de données
- **OBLIGATION**: Tests de régression automatisés
- **OBLIGATION**: Validation des seuils de qualité par source

### Métriques de Qualité Actuelles (Validées 28/01/2025)
```python
# Seuils atteints par source (tests concrets)
CURRENT_PERFORMANCE = {
    "emploi_tg": {"urls_extracted": 25, "success_rate": 1.0, "status": "✅ EXCELLENT"},
    "anpetogo": {"urls_extracted": 15, "success_rate": 1.0, "status": "✅ EXCELLENT"},
    "emploitogo_info": {"urls_extracted": 64, "success_rate": 1.0, "status": "✅ EXCELLENT"},
    "yop_lfrii": {"urls_extracted": 35, "success_rate": 1.0, "status": "✅ EXCELLENT"},
    "linkedin_togo": {"urls_extracted": 0, "success_rate": 0.0, "status": "⚠️ TIMEOUT"},
    "indeed_togo": {"urls_extracted": 0, "success_rate": 0.0, "status": "❌ HTTP 400"}
}
```

### Surveillance Continue (ACTIVE)
- ✅ **Import Health**: 13/13 modules importables (100%)
- ✅ **URL Extraction**: 139 URLs/cycle (4 sources stables)
- ✅ **Cache Performance**: 100% hit rate cycle 2+
- ✅ **CLI Functionality**: Opérationnelle sans erreur
- ⚠️ **Source Stability**: 4/6 sources stables (66.7%)

## 🛡️ RÈGLES DE MAINTENANCE ET ÉVOLUTION

### Avant Toute Modification
1. **OBLIGATOIRE**: Exécuter `test_imports_validation.py`
2. **OBLIGATOIRE**: Valider les tests de régression par source
3. **OBLIGATOIRE**: Vérifier la conformité aux steering files
4. **OBLIGATOIRE**: Documenter les changements architecturaux

### Gestion des Dépendances
- **INTERDICTION**: Ajout de dépendances sans validation d'impact
- **OBLIGATION**: Mise à jour du `requirements.txt` pour chaque nouvelle dépendance
- **OBLIGATION**: Test de compatibilité avec Python 3.11+
- **OBLIGATION**: Validation des versions de dépendances critiques

### Code Review Checklist (OBLIGATOIRE)
- [ ] Aucun import relatif à plus de 2 niveaux
- [ ] Tous les modules s'importent sans erreur
- [ ] Tests unitaires présents et passants
- [ ] Conformité aux conventions de nommage
- [ ] Documentation à jour
- [ ] Aucune régression sur les sources existantes

## 📊 MÉTRIQUES DE CONFORMITÉ

### Indicateurs de Santé Architecturale
- **Import Health**: 0 import relatif complexe autorisé
- **Test Coverage**: >90% pour les composants critiques
- **Source Reliability**: >85% de taux de succès par source
- **Code Quality**: 0 violation des règles de structure

### Alertes Automatiques
- 🚨 **CRITIQUE**: Échec d'import de module
- ⚠️ **ATTENTION**: Régression de plus de 15% sur une source
- 📊 **INFO**: Nouveau seuil de qualité atteint
- 🔧 **MAINTENANCE**: Mise à jour de dépendance requise

---

*Règles établies suite à l'audit technique critique du 24/07/2025*  
*Conformité obligatoire pour tous les développements futurs*