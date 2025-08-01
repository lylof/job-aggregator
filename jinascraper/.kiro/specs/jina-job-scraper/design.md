# Design Document - Scraper d'Offres d'Emploi Jina AI + Gemini

## Overview

Ce document décrit l'architecture technique du scraper d'offres d'emploi basé sur une approche hybride Jina AI + Google Gemini. Le système est conçu autour d'un workflow en deux étapes distinctes pour maximiser la qualité et la crédibilité des données extraites.

L'architecture exploite les forces spécifiques de chaque outil :
- **Jina Reader** : Extraction de contenu web propre et fiable
- **Google Gemini** : Structuration intelligente sans hallucination

## Architecture

### Vue d'Ensemble du Système

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPER JINA + GEMINI                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   SCHEDULER     │    │   ÉTAPE 1       │    │   ÉTAPE 2   │  │
│  │   (3x/jour)     │───▶│   EXPLORATION   │───▶│   ANALYSE   │  │
│  │                 │    │   (Jina Reader) │    │ (Jina+Gemini)│  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   SOURCES       │    │   CACHE REDIS   │    │  SUPABASE   │  │
│  │   (6 sites)     │    │   (Delta URLs)  │    │  (Storage)  │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture en Deux Étapes

#### Étape 1 : Exploration (Jina Reader)
```
Pages de Listing ──┐
                   │
emploi.tg         ├──► Jina Reader ──► URLs Extraction ──► Cache Redis
yop.l-frii.com    │    (gather_links)     (Nouvelles)        (Delta)
anpetogo.org      │
linkedin.com      │
indeed.com        │
emploitogo.info   ┘
```

#### Étape 2 : Analyse (Jina Reader + Gemini)
```
Nouvelles URLs ──► Jina Reader ──► Contenu Markdown ──► Gemini ──► JSON Structuré ──► Supabase
                   (ReaderLM-v2)     (Propre)          (Structured)   (Validé)        (Storage)
```

## Components and Interfaces

### 1. Scheduler Component
**Responsabilité** : Orchestration des cycles de scraping
- **Fréquence** : 3 exécutions par jour (08h00, 14h00, 20h00)
- **Interface** : Cron jobs ou scheduler intégré
- **Configuration** : Variables d'environnement pour les horaires

### 2. Source Configuration Architecture
**Responsabilité** : Gestion isolée des configurations des sources

#### Architecture de Configuration Robuste
```
jinascraper/
├── config/
│   ├── __init__.py
│   ├── base_config.py           # Configuration de base et paramètres globaux
│   ├── sources/                 # Un fichier par source
│   │   ├── __init__.py
│   │   ├── emploi_tg.py
│   │   ├── anpetogo.py
│   │   ├── emploitogo_info.py
│   │   ├── yop_lfrii.py
│   │   ├── linkedin_togo.py
│   │   └── indeed_togo.py
│   └── source_registry.py       # Registre centralisé des sources
└── services/
    ├── url_cleaners/            # Un fichier par source pour le nettoyage d'URL
    │   ├── __init__.py
    │   ├── emploi_tg_cleaner.py
    │   ├── anpetogo_cleaner.py
    │   └── ...
    └── url_cleaner.py           # Façade qui délègue aux nettoyeurs spécifiques
```

#### Configuration de Base
- **JinaReaderBaseConfig** : Paramètres par défaut pour Jina Reader
- **SourceBaseConfig** : Configuration de base pour une source de scraping
- Mécanisme de fusion explicite entre paramètres globaux et spécifiques

#### Configuration Spécifique par Source
- Chaque source a son propre fichier de configuration
- Isolation complète des paramètres entre sources
- Patterns d'extraction d'URL spécifiques à chaque source
- Fonctions de validation d'URL spécifiques à chaque source

#### Registre Centralisé des Sources
- **SourceRegistry** : Point d'accès unique pour toutes les sources
- Méthodes pour récupérer les sources par nom, type, etc.
- Fusion explicite des paramètres de base avec les paramètres spécifiques

#### Nettoyeurs d'URL Spécifiques
- Un fichier par source pour le nettoyage d'URL
- Isolation complète du code de nettoyage entre sources
- Façade centrale qui délègue aux nettoyeurs spécifiques

### 3. Jina Reader Service
**Responsabilité** : Interface avec l'API Jina Reader
- **Configuration Étape 1** :
  ```python
  exploration_config = {
      "gather_all_links_at_the_end": True,
      "remove_all_images": True,
      "css_selector_only": ".job-card, .offer-item, .job-listing",
      "timeout": 30
  }
  ```
- **Configuration Étape 2** :
  ```python
  analysis_config = {
      "use_reader_lm_v2": True,
      "css_selector_excluding": "header, footer, .ads, .sidebar",
      "with_generated_alt": True,
      "timeout": 60
  }
  ```

### 4. Gemini Service
**Responsabilité** : Structuration intelligente du contenu
- **Mode** : Structured Output pour éviter les hallucinations
- **Schéma de sortie** :
  ```json
  {
    "type": "object",
    "properties": {
      "titre": {"type": "string"},
      "entreprise": {"type": "string"},
      "description_complete": {"type": "string"},
      "lieu": {"type": "string"},
      "salaire": {"type": "string"},
      "type_contrat": {"type": "string"},
      "date_publication": {"type": "string"},
      "contact_email": {"type": "string"},
      "competences_requises": {"type": "array", "items": {"type": "string"}},
      "experience_requise": {"type": "string"},
      "source_url": {"type": "string"}
    },
    "required": ["titre", "entreprise", "source_url"]
  }
  ```

### 5. Cache Manager (Redis)
**Responsabilité** : Gestion du delta scraping
- **Clés** : Hash des URLs d'offres déjà traitées
- **TTL** : 7 jours pour éviter l'accumulation
- **Structure** :
  ```
  scraped:{url_hash} → "1" (TTL: 604800s)
  processed:{job_id} → job_data (TTL: 604800s)
  ```

### 6. Database Service (Supabase)
**Responsabilité** : Persistance des données structurées
- **Table principale** : `jobs`
- **Schéma** :
  ```sql
  CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id VARCHAR UNIQUE NOT NULL,
    titre VARCHAR NOT NULL,
    entreprise VARCHAR NOT NULL,
    description_complete TEXT,
    lieu VARCHAR,
    salaire VARCHAR,
    type_contrat VARCHAR,
    date_publication DATE,
    contact_email VARCHAR,
    competences_requises TEXT[],
    experience_requise VARCHAR,
    source_url VARCHAR NOT NULL,
    source_site VARCHAR NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
  );
  ```

## Data Models

### JobListing (Étape 1 - URLs découvertes)
```python
@dataclass
class JobListing:
    url: str
    source_site: str
    discovered_at: datetime
    title_preview: Optional[str] = None
    company_preview: Optional[str] = None
```

### JobOffer (Étape 2 - Données complètes)
```python
@dataclass
class JobOffer:
    titre: str
    entreprise: str
    description_complete: str
    lieu: Optional[str] = None
    salaire: Optional[str] = None
    type_contrat: Optional[str] = None
    date_publication: Optional[str] = None
    contact_email: Optional[str] = None
    competences_requises: List[str] = field(default_factory=list)
    experience_requise: Optional[str] = None
    source_url: str
    source_site: str
    raw_markdown: str
    processed_at: datetime
```

## Error Handling

### Stratégie de Gestion des Erreurs

#### Erreurs Jina Reader
- **4xx (Client)** : Log et passage à l'URL suivante
- **5xx (Serveur)** : Retry avec backoff exponentiel (max 3 tentatives)
- **429 (Rate Limit)** : Attente et retry selon les headers de l'API
- **Timeout** : Retry avec timeout augmenté

#### Erreurs Gemini
- **Structured Output invalide** : Log et sauvegarde du contenu brut
- **Quota dépassé** : Mise en queue et traitement différé
- **Erreur de parsing** : Fallback vers extraction basique

#### Erreurs Sources
- **Source indisponible** : Continue avec les autres sources
- **Structure changée** : Log pour mise à jour de configuration
- **Contenu vide** : Skip et log pour investigation

### Mécanismes de Résilience

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

#### Retry avec Backoff Exponentiel
```python
async def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return await func()
        except RetryableError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

## Testing Strategy

### Tests Unitaires
- **Jina Reader Service** : Mock des réponses API
- **Gemini Service** : Validation des schémas de sortie
- **Cache Manager** : Tests Redis en mémoire
- **Data Models** : Validation et sérialisation
- **Source Configuration** : Tests d'isolation entre sources

### Tests d'Intégration
- **Workflow complet** : Étape 1 → Étape 2 → Storage
- **Gestion des erreurs** : Simulation de pannes API
- **Performance** : Tests de charge avec volume réaliste
- **Source Registry** : Validation de l'isolation entre sources

### Tests End-to-End
- **Sources réelles** : Tests sur un sous-ensemble de sources
- **Données de production** : Validation sur échantillon
- **Monitoring** : Vérification des métriques

## Performance Considerations

### Optimisations Jina Reader
- **Étape 1** : Paramètres légers pour extraction rapide des URLs
- **Étape 2** : ReaderLM-v2 seulement pour pages complexes
- **Rate Limiting** : Respect strict des 5000 RPM premium
- **Parallélisation** : Traitement concurrent avec semaphore

### Optimisations Gemini
- **Batch Processing** : Groupement des requêtes quand possible
- **Prompt Optimization** : Minimisation des tokens d'entrée
- **Structured Output** : Éviter les tokens de formatage inutiles
- **Caching** : Cache des réponses pour contenus similaires

### Optimisations Base de Données
- **Index** : Sur source_url, created_at, is_active
- **Partitioning** : Par date pour les gros volumes
- **Archivage** : Déplacement des anciennes offres
- **Upsert** : Éviter les doublons avec ON CONFLICT

## Monitoring et Observabilité

### Métriques Clés
- **Étape 1** : URLs découvertes par source et par cycle
- **Étape 2** : Offres traitées avec succès vs échecs
- **Performance** : Latence moyenne par étape
- **Coûts** : Tokens consommés Jina + Gemini
- **Qualité** : Taux de complétude des champs extraits

### Alertes
- **Taux d'échec > 20%** : Alert critique
- **Aucune nouvelle offre** : Alert d'investigation
- **Dépassement budget tokens** : Alert financière
- **Source indisponible** : Alert opérationnelle

### Dashboards
- **Vue d'ensemble** : Métriques temps réel
- **Par source** : Performance détaillée
- **Coûts** : Suivi budgétaire
- **Qualité** : Analyse des données extraites

Cette architecture garantit un système robuste, scalable et maintenable pour l'agrégation d'offres d'emploi du Togo, en exploitant optimalement les capacités de Jina AI et Google Gemini, tout en assurant une isolation complète entre les sources pour éviter les régressions.