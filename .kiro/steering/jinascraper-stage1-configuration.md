# Configuration des Sources JinaScraper - Étape 1 (Stage 1)

## Vue d'ensemble

Ce document décrit la configuration des sources de données pour l'étape 1 du JinaScraper, qui se concentre sur l'exploration et la découverte d'URLs d'offres d'emploi. L'étape 1 utilise l'API Jina Reader pour extraire les liens vers les offres d'emploi depuis les pages de listing.

## Architecture de Configuration

### Structure Hiérarchique

La configuration suit une architecture en couches :

```
SourceStage1Config
├── SourceBaseConfig (informations de base)
├── Stage1JinaConfig (paramètres Jina spécifiques à l'étape 1)
└── jina_params (surcharges spécifiques à la source)
```

### Fichiers de Configuration

Chaque source a son propre fichier dans `jinascraper/config/sources/`:
- `linkedin_togo.py`
- `emploi_tg.py`
- `anpetogo.py`
- `indeed_togo.py`
- `yop_lfrii.py`
- `emploitogo_info.py`

## Configuration de Base (SourceBaseConfig)

### Paramètres Obligatoires

```python
@dataclass
class SourceBaseConfig:
    name: str                    # Nom de la source
    base_url: str               # URL de base du site
    listing_url: str            # URL de la page de listing des emplois
    source_type: SourceType     # Type de source (GOVERNMENT, PRIVATE, etc.)
    url_patterns: List[str]     # Patterns regex pour extraire les URLs
```

### Paramètres Optionnels

```python
    disabled: bool = False                      # Désactiver la source
    request_delay: float = 1.0                 # Délai entre les requêtes (secondes)
    requires_headers: bool = False             # Nécessite des headers personnalisés
    custom_headers: Dict[str, str] = {}        # Headers HTTP personnalisés
    expected_jobs_per_page: int = 20           # Nombre d'emplois attendus par page
    reliability_score: float = 0.8             # Score de fiabilité (0.0 à 1.0)
```

## Configuration Étape 1 (SourceStage1Config)

### Paramètres Spécifiques à l'Étape 1

```python
@dataclass
class SourceStage1Config:
    base: SourceBaseConfig                     # Configuration de base
    css_selector_jobs: Optional[str] = None    # Sélecteur CSS pour les liens d'emplois
    pagination_pattern: Optional[str] = None   # Pattern de pagination
    max_pages: int = 10                        # Nombre maximum de pages à traiter
    jina_params: Dict[str, Any] = {}          # Paramètres Jina spécifiques
```

## Configuration Jina Reader pour l'Étape 1

### Paramètres Généraux (Stage1JinaConfig)

Ces paramètres sont appliqués à toutes les sources par défaut :

```python
@dataclass
class Stage1JinaConfig:
    # Paramètres généraux optimisés pour l'étape 1
    engine: str = "browser"                    # X-Engine: browser
    no_cache: bool = True                      # X-No-Cache: true
    retain_images: str = "none"                # X-Retain-Images: none
    with_links_summary: str = "all"            # X-With-Links-Summary: all
    
    # CSS par défaut pour exclure les éléments non pertinents
    default_css_excluding: str = "header, footer, .ads, .sidebar, .navigation, .menu, .social-media"
```

### Paramètres Techniques de Base

```python
@dataclass
class JinaReaderTechnicalConfig:
    timeout: int = 30                          # Timeout en secondes
    retry_attempts: int = 3                    # Nombre de tentatives
    css_selector_only: Optional[str] = None    # Sélecteur CSS pour inclure
    css_selector_excluding: Optional[str] = None # Sélecteur CSS pour exclure
    css_selector_wait_for: Optional[str] = None  # Sélecteur CSS à attendre
```

## Paramètres Jina Spécifiques par Source

### Headers HTTP Jina

Les paramètres sont convertis en headers HTTP pour l'API Jina :

| Paramètre Python | Header HTTP | Description |
|------------------|-------------|-------------|
| `engine` | `X-Engine` | Moteur de rendu (browser/default) |
| `no_cache` | `X-No-Cache` | Désactiver le cache |
| `retain_images` | `X-Retain-Images` | Conservation des images |
| `with_links_summary` | `X-With-Links-Summary` | Résumé des liens |
| `target_selector` | `X-Target-Selector` | Sélecteur cible pour extraction |
| `remove_selector` | `X-Remove-Selector` | Sélecteur d'éléments à supprimer |
| `css_selector_only` | `X-CSS-Selector-Only` | Inclure uniquement ces éléments |
| `css_selector_excluding` | `X-CSS-Selector-Excluding` | Exclure ces éléments |
| `css_selector_wait_for` | `X-CSS-Selector-Wait-For` | Attendre cet élément |
| `timeout` | `X-Timeout` | Timeout de la requête |

### Paramètres Spécifiques par Source

#### LinkedIn Togo
```python
jina_params = {
    'target_selector': '.base-card__full-link',
    'timeout': '45',
    'css_selector_wait_for': '.base-card__full-link'
}
```

#### Emploi.tg
```python
jina_params = {
    'target_selector': 'h3 > a'
}
```

#### ANPE Togo
```python
jina_params = {
    'remove_selector': 'header#careerfy-header, div.jobsearch-banner-search, div.jobsearch-column-3.jobsearch-typo-wrap, footer#careerfy-footer',
    'target_selector': 'h2 > a'
}
```

#### Indeed Togo
```python
jina_params = {
    'css_selector_only': '.jobsearch-SerpJobCard, .job_seen_beacon',
    'timeout': '35'
}
```

#### YOP L'Frii
```python
jina_params = {
    'target_selector': 'h2.elementor-heading-title.elementor-size-default a'
}
```

#### EmploiTogo.info
```python
jina_params = {
    'target_selector': 'h3 > a'
}
```

## Patterns d'Extraction d'URLs

### Format des Patterns

Les patterns utilisent des expressions régulières pour extraire les URLs des offres d'emploi :

```python
# Exemple pour LinkedIn Togo
LINKEDIN_TOGO_URL_PATTERNS = [
    '(https://tg\\.linkedin\\.com/jobs/view/[^\\s<>"\\\']*)' 
]

# Exemple pour Emploi.tg
EMPLOI_TG_URL_PATTERNS = [
    '(https://www\\.emploi\\.tg/offre-emploi-togo/[^\\s<>"\\\']*)' 
]
```

### Caractères d'Échappement

- `\\.` : Point littéral
- `[^\\s<>"\\\']` : Tout caractère sauf espaces, <, >, ", \, '
- `*` : Zéro ou plusieurs occurrences

## Types de Sources

```python
class SourceType(str, Enum):
    GOVERNMENT = "government"      # Sources gouvernementales
    PRIVATE = "private"           # Sources privées
    INTERNATIONAL = "international" # Sources internationales
    NGO = "ngo"                   # Organisations non gouvernementales
```

## Exemple de Configuration Complète

```python
# Configuration de base
EMPLOI_TG_BASE_CONFIG = SourceBaseConfig(
    name="Emploi.tg",
    base_url="https://www.emploi.tg",
    listing_url="https://www.emploi.tg/recherche-jobs-togo",
    source_type=SourceType.GOVERNMENT,
    url_patterns=['(https://www\\.emploi\\.tg/offre-emploi-togo/[^\\s<>"\\\']*)'],
    request_delay=1.0,
    expected_jobs_per_page=20,
    reliability_score=0.9
)

# Configuration étape 1
EMPLOI_TG_STAGE1_CONFIG = SourceStage1Config(
    base=EMPLOI_TG_BASE_CONFIG,
    css_selector_jobs='h3 > a',
    max_pages=100,
    jina_params={
        'target_selector': 'h3 > a'
    }
)
```

## Validation et Tests

### Validation Automatique

Chaque configuration doit passer la validation :

```python
def validate(self) -> bool:
    """Valide que la configuration est complète."""
    required_fields = [self.name, self.base_url, self.listing_url]
    return all(field for field in required_fields)
```

### Tests de Régression

- Tests unitaires pour chaque source
- Validation des patterns d'extraction
- Tests de performance et de fiabilité
- Seuils de qualité minimum par source

## Métriques de Qualité

### Seuils Minimum par Source

```python
QUALITY_THRESHOLDS = {
    "linkedin_togo": {"min_urls": 35, "success_rate": 0.95},
    "anpetogo": {"min_urls": 12, "success_rate": 0.90},
    "emploi_tg": {"min_urls": 20, "success_rate": 0.80},
    "yop_lfrii": {"min_urls": 15, "success_rate": 0.85},
    "emploitogo_info": {"min_urls": 10, "success_rate": 0.90}
}
```

### Surveillance Continue

- Nombre d'URLs extraites par source
- Taux de succès du nettoyage d'URLs
- Temps de réponse des APIs externes
- Alertes en cas de régression > 20%

## Bonnes Pratiques

### Configuration des Sélecteurs CSS

1. **Spécificité** : Utiliser des sélecteurs spécifiques mais robustes
2. **Performance** : Éviter les sélecteurs trop complexes
3. **Maintenance** : Documenter les sélecteurs utilisés
4. **Tests** : Valider avec des données réelles

### Gestion des Timeouts

1. **Sites lents** : Augmenter le timeout (45-60s)
2. **Sites rapides** : Utiliser le timeout par défaut (30s)
3. **Surveillance** : Monitorer les temps de réponse

### Patterns d'URLs

1. **Précision** : Patterns spécifiques pour éviter les faux positifs
2. **Robustesse** : Gérer les variations d'URLs
3. **Validation** : Tester avec des URLs réelles

## Dépannage

### Problèmes Courants

1. **Aucune URL extraite** : Vérifier le `target_selector`
2. **Timeout fréquents** : Augmenter la valeur de timeout
3. **URLs invalides** : Réviser les patterns d'extraction
4. **Performance dégradée** : Optimiser les sélecteurs CSS

### Logs et Monitoring

- Logs structurés avec correlation IDs
- Métriques de performance par source
- Alertes automatiques sur les échecs
- Rapports de qualité quotidiens

---

*Documentation mise à jour pour l'architecture en couches du JinaScraper*  
*Conforme aux standards de qualité et de performance établis*