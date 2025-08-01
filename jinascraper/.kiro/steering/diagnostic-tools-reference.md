# Guide de Référence - Outils de Diagnostic JinaScraper

## 🎯 Vue d'ensemble

Ce guide présente les outils de diagnostic créés suite à la percée technique du 29 Juillet 2025. Ces outils permettent d'isoler et de diagnostiquer les problèmes dans le pipeline JinaScraper étape par étape.

## 🔍 Commandes de Diagnostic Disponibles

### 1. Diagnostic Stage 1 - Extraction d'URLs

#### Commande
```bash
python cli.py diagnose [OPTIONS]
```

#### Options
- `--sources TEXT` : Sources spécifiques à tester (séparées par virgules)
- `--verbose` : Logging détaillé avec informations de debug

#### Exemples d'utilisation
```bash
# Test d'une source spécifique
python cli.py diagnose --sources emploi_tg --verbose

# Test de plusieurs sources
python cli.py diagnose --sources emploi_tg,anpetogo,yop_lfrii --verbose

# Test automatique des sources disponibles
python cli.py diagnose --verbose
```

#### Ce que ça teste
- ✅ Extraction d'URLs depuis les pages de listing
- ✅ Validation de la propreté des URLs (détection des caractères parasites)
- ✅ Fonctionnement de l'API Jina Reader pour Stage 1
- ✅ Configuration des sources et des URL cleaners
- ✅ Performance et temps de réponse

#### Rapport généré
```
📊 RAPPORT DIAGNOSTIC STAGE 1 - EXTRACTION D'URLS
🎯 Sources testées: 1
✅ Sources fonctionnelles: 1/1
📊 Total URLs extraites: 25
⚠️  URLs malformées: 0
⏱️  Temps de traitement: 22.08s

📋 DÉTAIL PAR SOURCE:
✅ emploi_tg:
   URLs trouvées: 25
   URLs propres: 25

🔧 DIAGNOSTIC ET RECOMMANDATIONS:
✅ STAGE 1 FONCTIONNE CORRECTEMENT
🎯 PROCHAINE ÉTAPE: Tester Stage 2 avec ces URLs
```

### 2. Diagnostic Stage 2 - Extraction de Contenu

#### Commande
```bash
python cli.py diagnose2 [OPTIONS]
```

#### Options
- `--url TEXT` : URL spécifique à tester pour l'extraction de contenu
- `--source TEXT` : Nom de la source pour la configuration (défaut: emploi_tg)
- `--verbose` : Logging détaillé avec informations de debug

#### Exemples d'utilisation
```bash
# Test avec URL par défaut
python cli.py diagnose2 --verbose

# Test avec URL spécifique
python cli.py diagnose2 --url "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684" --verbose

# Test avec source différente
python cli.py diagnose2 --url "https://yop.l-frii.com/emploi/..." --source yop_lfrii --verbose
```

#### Ce que ça teste
- ✅ Extraction de contenu détaillé via Jina Reader
- ✅ Validation des données extraites (titre, entreprise, localisation)
- ✅ Test de l'enrichissement IA via Gemini
- ✅ Validation des modèles de données Pydantic
- ✅ Performance de l'extraction complète

#### Rapport généré
```
📊 RAPPORT DIAGNOSTIC STAGE 2 - EXTRACTION DE CONTENU
🎯 URL testée: https://www.emploi.tg/offre-emploi-togo/...
✅ Stage 2 global: ✅ SUCCÈS
📊 Jina Reader: ✅ OK
🤖 Gemini IA: ⚠️ PROBLÈME PARTIEL
⏱️  Temps de traitement: 15.23s

📋 DONNÉES EXTRAITES:
   Titre: Conseiller Clientèle Bilingue
   Entreprise: MAJOREL
   Localisation: Lomé
   Méthode: ExtractionMethod.JINA

🔧 DIAGNOSTIC ET RECOMMANDATIONS:
⚠️  PROBLÈME PARTIEL: Jina OK mais Gemini échoue
🔧 ACTION: Vérifier la configuration Gemini
```

## 🛠️ Utilisation Pratique

### Workflow de Diagnostic Recommandé

#### 1. Problème de Scraping Global
```bash
# Étape 1: Tester Stage 1 d'abord
python cli.py diagnose --sources emploi_tg --verbose

# Si Stage 1 OK, tester Stage 2 avec une URL propre
python cli.py diagnose2 --url "URL_OBTENUE_STAGE1" --verbose
```

#### 2. Problème sur une Source Spécifique
```bash
# Tester la source problématique isolément
python cli.py diagnose --sources SOURCE_PROBLEMATIQUE --verbose
```

#### 3. Problème d'Extraction de Contenu
```bash
# Tester directement avec une URL connue
python cli.py diagnose2 --url "URL_PROBLEMATIQUE" --source SOURCE_NAME --verbose
```

### Interprétation des Résultats

#### Stage 1 - Codes de Statut
- ✅ **SUCCESS** : URLs extraites et propres
- ❌ **FAILED** : Aucune URL extraite
- ⚠️ **PARTIAL** : URLs extraites mais certaines malformées

#### Stage 2 - Codes de Statut
- ✅ **SUCCESS** : Contenu extrait et enrichi
- ❌ **JINA_FAILED** : Problème d'extraction Jina Reader
- ⚠️ **GEMINI_FAILED** : Extraction OK mais enrichissement échoué

### Actions Recommandées par Type de Problème

#### URLs Malformées (Stage 1)
```
🔧 ACTION: Corriger les URL cleaners pour nettoyer les caractères parasites
```
- Vérifier les patterns regex dans les URL cleaners
- Tester les expressions régulières avec des URLs réelles
- Valider la logique de nettoyage

#### Jina Reader Échoue (Stage 1 ou 2)
```
🔧 ACTION: Vérifier la configuration des sources et l'API Jina
```
- Vérifier la clé API Jina
- Contrôler les paramètres de configuration (timeouts, sélecteurs CSS)
- Tester manuellement l'URL avec l'API Jina

#### Gemini Enrichissement Échoue (Stage 2)
```
🔧 ACTION: Vérifier la configuration Gemini
```
- Vérifier la clé API Gemini
- Contrôler les prompts d'enrichissement
- Valider les modèles de données Pydantic

## 🔧 Dépannage Avancé

### Logs Détaillés
Utiliser `--verbose` pour obtenir des informations détaillées :
- URLs testées et leurs réponses
- Temps de traitement par étape
- Erreurs détaillées avec stack traces
- Métriques de performance

### Variables d'Environnement
Vérifier les variables d'environnement critiques :
```bash
# Clés API
JINA_API_KEY=your_jina_key
GEMINI_API_KEY=your_gemini_key

# Configuration Redis
REDIS_URL=redis://localhost:6379/0
USE_FAKE_REDIS=true
```

### Fichiers de Configuration
Vérifier les fichiers de configuration des sources :
- `jinascraper/config/sources/*.py`
- Paramètres Jina spécifiques par source
- Sélecteurs CSS et patterns d'URLs

## 📊 Métriques et Performance

### Seuils de Performance Attendus
- **Stage 1** : < 30s pour 25 URLs
- **Stage 2** : < 5s par URL
- **Jina Reader** : < 3s par requête
- **Gemini** : < 10s par enrichissement

### Métriques de Qualité
- **URLs propres** : > 95%
- **Extraction réussie** : > 90%
- **Enrichissement** : > 80%

## 🎯 Intégration dans le Workflow

### Tests Automatisés
Intégrer ces commandes dans les tests automatisés :
```bash
# Dans les scripts de CI/CD
python cli.py diagnose --sources emploi_tg
if [ $? -eq 0 ]; then
    echo "Stage 1 OK"
    python cli.py diagnose2 --url "URL_TEST"
fi
```

### Monitoring de Production
Utiliser ces outils pour le monitoring :
- Tests de santé réguliers
- Alertes sur les échecs de diagnostic
- Métriques de performance continues

---

**Date de création** : 29 Juillet 2025  
**Version** : 1.0  
**Statut** : ✅ Opérationnel et validé  
**Maintenance** : Mise à jour selon l'évolution des fonctionnalités