---
name: "Pre-Commit Validation"
description: "Validates imports and source functionality before commits - Based on 25/07/2025 execution diagnosis"
trigger: "manual"
workingDirectory: "jinascraper"
---

# Pre-Commit Validation Hook

**Basé sur le diagnostic par l'exécution du 25/07/2025**

Ce hook effectue des tests de validation critiques avant tout commit pour éviter les régressions identifiées lors de l'audit approfondi.

## Smoke Tests Obligatoires

### 1. Import Validation (CRITIQUE)

Valide que les 6 fichiers de nettoyeurs problématiques s'importent correctement :

```bash
python -c "
import sys
from pathlib import Path

# Test des imports critiques identifiés
try:
    from jinascraper.services.url_cleaners.emploitogo_info_cleaner import clean_emploitogo_info_urls
    from jinascraper.services.url_cleaners.yop_lfrii_cleaner import clean_yop_lfrii_urls
    from jinascraper.services.url_cleaners.linkedin_togo_cleaner import clean_linkedin_togo_urls
    from jinascraper.services.url_cleaners.indeed_togo_cleaner import clean_indeed_togo_urls
    from jinascraper.services.url_cleaners.emploi_tg_cleaner import clean_emploi_tg_urls
    from jinascraper.services.url_cleaners.anpetogo_cleaner import clean_anpe_urls
    print('✅ All critical imports successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"
```

### 2. Source Functionality Test (CRITIQUE)

Exécute le test principal pour valider le fonctionnement des sources :

```bash
python tests/test_stage1_new_architecture.py
```

### 3. Success Criteria (Basés sur les résultats du 25/07/2025)

**Seuils Minimum Obligatoires :**
- ✅ **0 ImportError** autorisé dans tout le système
- ✅ **Minimum 3/5 sources** avec URLs > 0
- ✅ **LinkedIn Togo** : ≥35 URLs (actuellement 40)
- ✅ **ANPE Togo** : ≥12 URLs (actuellement 15)
- ✅ **Emploi.tg** : ≥20 URLs (actuellement 25)

**Seuils Critiques à Réparer :**
- 🚨 **EmploiTogo.info** : ≥10 URLs (actuellement 0 - CRITIQUE)
- 🚨 **YOP L-FRII** : ≥15 URLs (actuellement 0 - CRITIQUE)

### 4. Validation Rapide des Patterns Regex

Test rapide des nettoyeurs critiques avec URLs réelles :

```bash
python -c "
# Test EmploiTogo.info avec URL réelle
from jinascraper.services.url_cleaners.emploitogo_info_cleaner import is_valid_emploitogo_info_url
test_url = 'https://www.emploitogo.info/locdi-caritas-togo-recrute-07-08-2025/'
if is_valid_emploitogo_info_url(test_url):
    print('✅ EmploiTogo.info patterns fixed')
else:
    print('❌ EmploiTogo.info patterns still broken')

# Test YOP L-FRII avec URL réelle  
from jinascraper.services.url_cleaners.yop_lfrii_cleaner import is_valid_yop_lfrii_url
test_url = 'https://yop.l-frii.com/emploi/recrutement-a-lunesco-24-juillet-2025/'
if is_valid_yop_lfrii_url(test_url):
    print('✅ YOP L-FRII patterns fixed')
else:
    print('❌ YOP L-FRII patterns still broken')
"
```

## Failure Actions

### Si Import Validation Échoue
1. **COMMIT IMMÉDIATEMENT BLOQUÉ**
2. Corriger les imports relatifs dans les fichiers identifiés
3. Remplacer `from ...utils.type_helpers` par `from jinascraper.utils.type_helpers`
4. Re-exécuter le hook jusqu'au succès

### Si Source Functionality Échoue
1. **COMMIT IMMÉDIATEMENT BLOQUÉ**
2. Identifier la source en échec
3. Corriger les patterns regex du nettoyeur correspondant
4. Valider avec les URLs réelles extraites
5. Re-exécuter le hook jusqu'au succès

### Si Moins de 3/5 Sources Fonctionnelles
1. **COMMIT BLOQUÉ**
2. Consulter le PLAN_DE_BATAILLE_V2.md
3. Appliquer les corrections spécifiques par source
4. Priorité absolue : EmploiTogo.info et YOP L-FRII

## Intégration avec le Développement

**Exécuter ce hook OBLIGATOIREMENT :**
- Avant tout commit touchant les nettoyeurs d'URL
- Avant tout commit touchant les configurations de sources
- Avant toute release ou déploiement
- Après toute modification des imports
- Hebdomadairement comme contrôle de routine

## Historique des Problèmes Identifiés

**25/07/2025 - Diagnostic par l'exécution :**
- 6 fichiers avec imports relatifs cassés
- EmploiTogo.info : 0/15 URLs (patterns inadéquats)
- YOP L-FRII : 0/23 URLs (patterns inadéquats)
- LinkedIn Togo : 40/40 URLs (fonctionnel)
- ANPE Togo : 15/15 URLs (fonctionnel)
- Emploi.tg : 25/126 URLs (fonctionnel)

---

*Hook créé suite au diagnostic approfondi par l'exécution du 25/07/2025*  
*Objectif : Prévenir toute régression sur les imports et la fonctionnalité des sources*