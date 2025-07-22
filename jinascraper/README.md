# Jina Job Scraper - Orchestrateur Principal

L'orchestrateur principal (`ScrapingOrchestrator`) coordonne le workflow complet de scraping en deux étapes :

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPING ORCHESTRATOR                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   ÉTAPE 1       │    │   ÉTAPE 2       │    │   STORAGE   │  │
│  │   EXPLORATION   │───▶│   ANALYSE       │───▶│   DATABASE  │  │
│  │   (Jina Reader) │    │ (Jina+Gemini)   │    │  (Supabase) │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   SOURCES       │    │   CACHE REDIS   │                    │
│  │   (6 sites)     │    │   (Delta URLs)  │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Utilisation

### 1. Via le CLI principal

```bash
# Lancer un cycle complet
python -m jinascraper.main scrape

# Mode dry-run (sans sauvegarde)
python -m jinascraper.main scrape --dry-run

# Tester les services
python -m jinascraper.main test-services

# Tester une source spécifique
python -m jinascraper.main test-source emploi_tg
```

### 2. Via le script de test

```bash
# Test Stage 1 uniquement (découverte URLs)
python jinascraper/test_orchestrator.py --mode stage1

# Test cycle complet
python jinascraper/test_orchestrator.py --mode full
```

### 3. Via l'API Python

```python
import asyncio
from jinascraper import ScrapingOrchestrator

async def main():
    async with ScrapingOrchestrator() as orchestrator:
        # Cycle complet
        result = await orchestrator.run_full_cycle()
        print(f"Jobs trouvés: {result.jobs_found}")
        print(f"Jobs traités: {result.jobs_processed}")
        
        # Ou étapes séparées
        stage1 = await orchestrator.run_stage1_exploration()
        stage2 = await orchestrator.run_stage2_analysis(stage1["new_urls"])

asyncio.run(main())
```

## Workflow Détaillé

### Étape 1 : Exploration
1. **Sources actives** : Récupère toutes les sources configurées et actives
2. **Extraction parallèle** : Utilise Jina Reader pour extraire les URLs de toutes les sources en parallèle
3. **Delta filtering** : Utilise Redis pour filtrer les URLs déjà traitées
4. **Cache update** : Marque les nouvelles URLs comme découvertes

### Étape 2 : Analyse
1. **Traitement par batch** : Traite les URLs par lots de 10 pour gérer la mémoire
2. **Pipeline Jina → Gemini** : 
   - Jina Reader extrait le contenu Markdown
   - Gemini structure les données en JSON
3. **Validation qualité** : Vérifie la complétude des données extraites
4. **Sauvegarde** : Stocke les jobs structurés dans Supabase

## Configuration

Les services sont configurés via les variables d'environnement dans `.env` :

```env
# Jina AI
JINA_API_KEY=your_jina_key
JINA_BASE_URL=https://r.jina.ai/

# Google Gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Métriques et Monitoring

L'orchestrateur fournit des métriques détaillées :

- **URLs découvertes** par source
- **Jobs traités** avec succès
- **Temps de traitement** par étape
- **Taux de succès** global
- **Erreurs** détaillées par type

## Gestion des Erreurs

- **Retry automatique** avec backoff exponentiel
- **Circuit breaker** pour les sources défaillantes
- **Fallback gracieux** en cas d'échec partiel
- **Logging structuré** pour le debugging

## Sources Configurées

1. **emploi.tg** - Principal site d'emploi togolais
2. **anpetogo.org** - Service public de l'emploi (ANPE)
3. **yop.l-frii.com** - ONG et secteur humanitaire
4. **emploitogo.info** - Actualités emploi
5. **linkedin.com** - LinkedIn Togo
6. **indeed.com** - Indeed Togo (temporairement désactivé)

## Performance et Sécurité (Phase 4)

- **Performance Monitoring** : Suivi des temps d'exécution des opérations critiques
- **Batch Processing** : Traitement par lots avec contrôle de concurrence et limitation de débit
- **Caching Optimization** : Mise en cache intelligente avec éviction LRU
- **URL Validation** : Validation robuste des URL pour prévenir les attaques
- **Data Sanitization** : Sanitisation des données pour supprimer le contenu dangereux
- **Security Auditing** : Système d'audit pour suivre les événements de sécurité
- **Plugin System** : Système de plugins extensible pour ajouter des fonctionnalités

Pour plus de détails sur les améliorations de la Phase 4, consultez [PHASE4_README.md](./PHASE4_README.md) et [ARCHITECTURE.md](./ARCHITECTURE.md).