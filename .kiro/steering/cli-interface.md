# Interface CLI JinaScraper - Guide Complet

## 🖥️ Vue d'ensemble

Le JinaScraper dispose d'une interface en ligne de commande complète et fonctionnelle accessible via `cli.py`. Cette CLI utilise l'architecture core/ moderne avec injection de dépendances et monitoring intégré.

## 🚀 Utilisation de Base

### Commande Principale
```bash
python cli.py scrape [OPTIONS]
```

### Options Disponibles
```bash
--sources TEXT       # Sources spécifiques (séparées par virgules)
--max-urls INTEGER   # Maximum d'URLs à traiter par source (défaut: 100)
--dry-run           # Mode test sans sauvegarde des données
--verbose           # Logging détaillé avec informations de debug
--quiet             # Logging minimal (erreurs uniquement)
--show-urls INTEGER # Nombre d'URLs d'exemple à afficher (défaut: 3)
--no-color          # Désactiver la sortie colorée
--help              # Afficher l'aide
```

## 📋 Exemples d'Utilisation

### Scraping Complet
```bash
# Scraping de toutes les sources avec logging normal
python cli.py scrape

# Scraping avec logging détaillé
python cli.py scrape --verbose

# Mode silencieux (erreurs uniquement)
python cli.py scrape --quiet
```

### Scraping Ciblé
```bash
# Source spécifique
python cli.py scrape --sources emploi_tg

# Plusieurs sources
python cli.py scrape --sources emploi_tg,anpetogo,yop_lfrii

# Limitation du nombre d'URLs
python cli.py scrape --sources emploi_tg --max-urls 50
```

### Mode Test
```bash
# Dry-run (pas de sauvegarde)
python cli.py scrape --dry-run --verbose

# Test avec source spécifique
python cli.py scrape --sources emploi_tg --dry-run --show-urls 5
```

## 🏗️ Architecture CLI

### Flux d'Exécution
```
cli.py (Click interface)
    ↓
JinaScraperApp (app.py)
    ↓
ScrapingOrchestrator (core/orchestrator.py)
    ↓
Services (Jina, Gemini, Cache, Database)
```

### Composants Principaux

#### 1. **cli.py** - Interface Click
- Définition des commandes et options
- Validation des paramètres d'entrée
- Gestion des erreurs et codes de sortie

#### 2. **app.py** - Application Wrapper
- `JinaScraperApp` : Classe principale d'orchestration
- `ScrapeOptions` : Configuration des options CLI
- `ScrapeResults` : Résultats structurés
- Enhanced logger intégré

#### 3. **core/orchestrator.py** - Logique Métier
- Workflow en 2 étapes (Exploration + Analyse)
- Injection de dépendances
- Context manager async
- Monitoring de performance

## 📊 Sortie et Logging

### Démarrage Automatique
```
2025-01-28 18:13:28 [info] Registered source configuration for anpetogo
2025-01-28 18:13:28 [info] Registered source configuration for emploi_tg
2025-01-28 18:13:28 [info] Registered source configuration for emploitogo_info
2025-01-28 18:13:28 [info] Registered source configuration for yop_lfrii
2025-01-28 18:13:28 [info] Registered source configuration for linkedin_togo
2025-01-28 18:13:28 [info] Registered source configuration for indeed_togo
2025-01-28 18:13:28 [info] Initialized source registry with 6 sources
2025-01-28 18:13:28 [info] Registered URL cleaner for source: anpetogo
2025-01-28 18:13:28 [info] Registered URL cleaner for source: emploitogo_info
2025-01-28 18:13:28 [info] Registered URL cleaner for source: emploi_tg
2025-01-28 18:13:28 [info] Registered URL cleaner for source: indeed_togo
2025-01-28 18:13:28 [info] Registered URL cleaner for source: linkedin_togo
2025-01-28 18:13:28 [info] Registered URL cleaner for source: yop_lfrii
```

### Rapport Final
```
============================================================
🔍 JINASCRAPER REPORT
============================================================
✅ Status: SUCCESS
📊 Jobs Processed: 45
🌐 Sources Processed: 4
⏱️  Processing Time: 147.23s

📋 Configuration:
   Sources Filter: All
   Max URLs: 100
   Dry Run: False
   Verbose: True

📈 Detailed Metrics:
   Success Rate: 89.2%
   Jobs Found: 139
   Processing Time: 147.23s
   Source Site: Multiple
   Timestamp: 2025-01-28T18:15:42
============================================================
```

## ⚙️ Configuration

### Variables d'Environnement
La CLI charge automatiquement la configuration depuis :
- `jinascraper/.env` - Configuration locale
- Variables d'environnement système

### Sources Configurées
- ✅ **emploi_tg** (Emploi.tg) - Gouvernemental
- ✅ **anpetogo** (ANPE Togo) - Gouvernemental
- ✅ **emploitogo_info** (EmploiTogo.info) - Privé
- ✅ **yop_lfrii** (YOP L-FRII) - Privé
- ⚠️ **linkedin_togo** (LinkedIn Togo) - Instable
- ❌ **indeed_togo** (Indeed Togo) - Problématique

## 🔧 Dépannage

### Problèmes Courants

#### 1. Erreur d'Import
```bash
ImportError: attempted relative import beyond top-level package
```
**Solution** : Exécuter depuis le répertoire racine du projet

#### 2. Sources Indisponibles
```bash
❌ LinkedIn Togo: Timeout
❌ Indeed Togo: HTTP 400
```
**Solution** : Utiliser `--sources` pour exclure les sources problématiques

#### 3. Problèmes de Configuration
```bash
ERROR: Configuration not found
```
**Solution** : Vérifier la présence du fichier `.env` dans `jinascraper/`

### Commandes de Diagnostic
```bash
# Test des imports
python jinascraper/test_imports_fixed.py

# Vérification Redis
python jinascraper/check_redis_simple.py

# Audit complet
python jinascraper/audit_complet_janvier_2025.py
```

## 🎯 Codes de Sortie

- **0** : Succès complet
- **1** : Erreur générale ou interruption utilisateur
- **2** : Erreur de configuration
- **3** : Erreur de validation des données

## 🚀 Fonctionnalités Avancées

### Enhanced Logger
- **Couleurs** : Sortie colorée par défaut (désactivable avec `--no-color`)
- **Niveaux** : Debug, Info, Warning, Error
- **Contexte** : Correlation IDs pour traçabilité
- **Métriques** : Temps de traitement et statistiques

### Monitoring Intégré
- **Performance** : Suivi temps réel des opérations
- **Sécurité** : Validation des URLs et audit
- **Cache** : Statistiques Redis et hit rates
- **Erreurs** : Logging structuré avec stack traces

### Gestion d'Erreurs
- **Graceful degradation** : Continue même si certaines sources échouent
- **Retry automatique** : Tentatives multiples pour les erreurs temporaires
- **Fallback** : FakeRedis si Redis indisponible
- **Interruption propre** : Gestion de Ctrl+C

## 📚 Intégration avec l'Écosystème

### Hooks Kiro
- **Pre-commit** : Validation automatique avant commit
- **Post-deploy** : Tests de régression après déploiement
- **Monitoring** : Alertes sur dégradation de performance

### Tests Automatisés
- **Import validation** : `test_imports_fixed.py`
- **Architecture** : `test_architecture_complete.py`
- **Sources** : Tests de régression par source

### Documentation
- **Rapports** : Génération automatique de rapports d'audit
- **Métriques** : Historique des performances
- **Logs** : Archivage structuré des exécutions

---

**Dernière mise à jour** : 28 Janvier 2025  
**Version CLI** : 1.0 - Production Ready  
**Statut** : ✅ Pleinement Fonctionnelle