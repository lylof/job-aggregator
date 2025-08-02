# Design Document - Cartographie Architecture Système JinaScraper

## Overview

Cette analyse technique vise à créer une cartographie complète et précise de l'architecture du système JinaScraper, en se basant sur des traces d'exécution réelles et une analyse approfondie du code. L'objectif est de fournir une compréhension totale du système avec une grande assurance.

## Architecture

### Méthodologie d'Analyse

1. **Analyse Statique** : Examen des imports, dépendances et structure des fichiers
2. **Analyse Dynamique** : Traces d'exécution réelles avec logs détaillés
3. **Validation Croisée** : Vérification des configurations et comportements observés
4. **Documentation Technique** : Création de diagrammes et flux détaillés

### Approche de Cartographie

#### Phase 1 : Identification des Composants Core
- Analyse des fichiers de base (cli.py, app.py, core/)
- Identification des services principaux
- Mapping des interfaces et adapters

#### Phase 2 : Analyse Spécifique emploi.tg
- Trace complète du flux d'exécution
- Identification de tous les fichiers impliqués
- Analyse des configurations spécifiques

#### Phase 3 : Comparaison Multi-Sources
- Analyse des autres sources (anpetogo, yop_lfrii, etc.)
- Identification des patterns communs et différences
- Documentation des variations de configuration

#### Phase 4 : Validation et Documentation
- Tests de validation des flux identifiés
- Création de diagrammes d'architecture
- Documentation technique complète

## Components and Interfaces

### Structure de la Cartographie

```
JinaScraper System Map
├── Entry Points
│   ├── CLI Interface (cli.py)
│   └── Application Wrapper (app.py)
├── Core Architecture
│   ├── Orchestrator (core/orchestrator.py)
│   ├── Service Adapters (core/service_adapters.py)
│   └── Interfaces (core/interfaces.py)
├── Configuration System
│   ├── Base Configuration (config/base_config.py)
│   ├── Source Registry (config/source_registry.py)
│   └── Source-Specific Configs (config/sources/)
├── Services Layer
│   ├── Stage 1 Services (listing_scraper.py, jina_client.py)
│   ├── Stage 2 Services (detail_scraper.py, gemini_service.py)
│   └── Support Services (cache_manager.py, url_cleaners/)
└── Data Models (models.py)
```

### Flux d'Exécution Détaillé

#### Démarrage Système
1. **cli.py** → Parse des arguments CLI
2. **app.py** → Initialisation JinaScraperApp
3. **core/orchestrator.py** → Création ScrapingOrchestrator
4. **config/source_registry.py** → Chargement des sources
5. **config/sources/*.py** → Configuration spécifique par source

#### Traitement emploi.tg - Stage 1
1. **config/sources/emploi_tg.py** → Configuration chargée
2. **services/listing_scraper.py** → Extraction URLs listing
3. **services/jina_client.py** → Appel API Jina Reader
4. **services/url_cleaners/emploi_tg_cleaner.py** → Nettoyage URLs
5. **services/cache_manager.py** → Delta scraping

#### Traitement emploi.tg - Stage 2
1. **services/detail_scraper.py** → Extraction contenu détaillé
2. **services/jina_client.py** → Appel API Jina Reader (Stage 2)
3. **services/gemini_service.py** → Structuration IA
4. **services/openrouter_service.py** → Fallback IA
5. **services/database_service.py** → Sauvegarde données

## Data Models

### Configuration Hierarchy

```python
# Base Configuration Classes
SourceBaseConfig
├── name, base_url, listing_url
├── source_type, url_patterns
└── technical_settings

SourceStage1Config
├── base: SourceBaseConfig
├── jina_config: Stage1JinaConfig
└── stage1_specific_params

SourceStage2Config
├── base: SourceBaseConfig
├── jina_config: Stage2JinaConfig
└── stage2_specific_params
```

### Service Architecture

```python
# Core Services
ScrapingOrchestrator
├── content_extractor: JinaContentExtractorAdapter
├── job_structurer: GeminiJobStructurerAdapter
├── cache_manager: RedisCacheManagerAdapter
└── database_service: DatabaseServiceAdapter

# Service Adapters Pattern
ContentExtractorInterface → JinaContentExtractorAdapter → JinaClient
JobStructurerInterface → GeminiJobStructurerAdapter → GeminiService
CacheManagerInterface → RedisCacheManagerAdapter → CacheManager
```

## Error Handling

### Points de Défaillance Identifiés

1. **Configuration Loading** : Fichiers de configuration manquants ou malformés
2. **API External Services** : Quotas dépassés, timeouts, erreurs réseau
3. **URL Cleaning** : Patterns invalides, URLs malformées
4. **Data Processing** : Erreurs de parsing, validation Pydantic
5. **Cache Operations** : Redis indisponible, erreurs de sérialisation

### Stratégies de Récupération

1. **Fallback Configurations** : Configurations par défaut si spécifiques manquantes
2. **Service Degradation** : FakeRedis si Redis indisponible
3. **API Fallbacks** : OpenRouter si Gemini échoue
4. **Data Preservation** : Sauvegarde données brutes si structuration échoue

## Testing Strategy

### Validation de la Cartographie

1. **Tests de Trace** : Validation des flux d'exécution identifiés
2. **Tests de Configuration** : Vérification du chargement des configs
3. **Tests d'Intégration** : Validation des interactions entre composants
4. **Tests de Performance** : Mesure des temps de traitement par composant

### Métriques de Validation

- **Couverture des Fichiers** : % de fichiers système identifiés et documentés
- **Précision des Flux** : Correspondance entre flux documentés et traces réelles
- **Complétude des Configurations** : % de paramètres de configuration documentés
- **Validation Croisée** : Cohérence entre analyse statique et dynamique

## Implementation Plan

### Phase 1 : Analyse Core (2-3 jours)
1. Trace complète du démarrage système
2. Identification des composants core et leurs rôles
3. Mapping des interfaces et dépendances
4. Documentation des patterns architecturaux

### Phase 2 : Analyse emploi.tg (1-2 jours)
1. Trace détaillée du traitement emploi.tg
2. Identification de tous les fichiers impliqués
3. Analyse des configurations spécifiques
4. Documentation des flux Stage 1 et Stage 2

### Phase 3 : Analyse Multi-Sources (2-3 jours)
1. Analyse comparative des autres sources
2. Identification des patterns communs et différences
3. Documentation des variations de configuration
4. Analyse des performances par source

### Phase 4 : Documentation et Validation (1-2 jours)
1. Création des diagrammes d'architecture
2. Rédaction de la documentation technique
3. Tests de validation des flux identifiés
4. Révision et finalisation

## Success Criteria

- **Cartographie Complète** : 100% des fichiers système identifiés et documentés
- **Flux Validés** : Correspondance parfaite entre documentation et traces réelles
- **Configurations Documentées** : Toutes les configurations sources analysées
- **Architecture Claire** : Diagrammes et documentation technique précis
- **Points d'Amélioration** : Identification des optimisations possibles