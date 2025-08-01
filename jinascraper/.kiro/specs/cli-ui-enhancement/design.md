# Design Document - Amélioration Interface CLI JinaScraper

## Overview

Ce document décrit la conception d'une interface CLI moderne et esthétique pour le JinaScraper. L'objectif est de transformer l'expérience utilisateur actuelle (logs techniques bruts) en une interface professionnelle, informative et visuellement attrayante.

## Architecture

### Composants Principaux

```
Enhanced CLI Architecture
├── cli.py (Point d'entrée - inchangé)
├── app.py (Application wrapper - amélioré)
├── utils/
│   ├── enhanced_logger.py (Existant - étendu)
│   ├── cli_display.py (Nouveau - Affichage principal)
│   ├── progress_manager.py (Nouveau - Barres de progression)
│   ├── report_generator.py (Nouveau - Rapports visuels)
│   └── terminal_utils.py (Nouveau - Utilitaires terminal)
└── core/orchestrator.py (Orchestrateur - hooks ajoutés)
```

### Flux d'Affichage

```
1. Startup Screen (Header + Loading)
2. Configuration Summary (Sources + Status)
3. Real-time Progress (Stage 1 & 2)
4. Live Updates (URLs found, Cache hits, Errors)
5. Final Report (Professional summary)
6. Interactive Options (Save, Export, etc.)
```

## Components and Interfaces

### 1. CLIDisplay - Gestionnaire d'Affichage Principal

```python
class CLIDisplay:
    """Gestionnaire principal de l'affichage CLI moderne."""
    
    def __init__(self, use_colors: bool = True, verbose: bool = False):
        self.use_colors = use_colors
        self.verbose = verbose
        self.terminal_width = self._get_terminal_width()
        self.progress_manager = ProgressManager()
        self.report_generator = ReportGenerator()
    
    def show_startup_header(self) -> None:
        """Affiche le header de démarrage avec logo ASCII."""
        
    def show_loading_progress(self, message: str, progress: float) -> None:
        """Affiche une barre de progression pour le chargement."""
        
    def show_configuration_summary(self, sources: List[Dict], cleaners: List[str]) -> None:
        """Affiche un résumé visuel de la configuration."""
        
    def show_stage_header(self, stage: str, description: str) -> None:
        """Affiche l'en-tête d'une étape avec séparateur visuel."""
        
    def update_progress(self, source: str, progress: float, urls_found: int) -> None:
        """Met à jour la progression en temps réel."""
        
    def show_cache_stats(self, hit_rate: float, savings: int) -> None:
        """Affiche les statistiques de cache de manière visuelle."""
        
    def show_error(self, error_type: str, message: str, suggestions: List[str]) -> None:
        """Affiche une erreur avec suggestions de résolution."""
        
    def show_final_report(self, results: Dict[str, Any]) -> None:
        """Génère et affiche le rapport final professionnel."""
```

### 2. ProgressManager - Gestionnaire de Progression

```python
class ProgressManager:
    """Gère les barres de progression et indicateurs visuels."""
    
    def __init__(self, terminal_width: int = 80):
        self.terminal_width = terminal_width
        self.active_bars: Dict[str, ProgressBar] = {}
    
    def create_progress_bar(self, name: str, total: int, description: str) -> str:
        """Crée une nouvelle barre de progression."""
        
    def update_progress_bar(self, name: str, current: int, message: str = "") -> None:
        """Met à jour une barre de progression existante."""
        
    def complete_progress_bar(self, name: str, success: bool = True) -> None:
        """Marque une barre de progression comme terminée."""
        
    def render_all_bars(self) -> str:
        """Rend toutes les barres de progression actives."""
```

### 3. ReportGenerator - Générateur de Rapports

```python
class ReportGenerator:
    """Génère des rapports visuels et professionnels."""
    
    def generate_startup_report(self, config: Dict[str, Any]) -> str:
        """Génère le rapport de démarrage."""
        
    def generate_progress_summary(self, stage: str, metrics: Dict[str, Any]) -> str:
        """Génère un résumé de progression pour une étape."""
        
    def generate_final_report(self, results: Dict[str, Any]) -> str:
        """Génère le rapport final avec graphiques ASCII."""
        
    def generate_error_report(self, errors: List[Dict[str, Any]]) -> str:
        """Génère un rapport d'erreurs avec suggestions."""
        
    def create_ascii_chart(self, data: Dict[str, int], title: str) -> str:
        """Crée un graphique ASCII simple."""
        
    def create_status_table(self, items: List[Dict[str, Any]]) -> str:
        """Crée un tableau de statut formaté."""
```

### 4. TerminalUtils - Utilitaires Terminal

```python
class TerminalUtils:
    """Utilitaires pour la gestion du terminal."""
    
    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        """Obtient la taille du terminal."""
        
    @staticmethod
    def supports_colors() -> bool:
        """Vérifie si le terminal supporte les couleurs."""
        
    @staticmethod
    def clear_line() -> None:
        """Efface la ligne courante."""
        
    @staticmethod
    def move_cursor_up(lines: int) -> None:
        """Déplace le curseur vers le haut."""
        
    @staticmethod
    def hide_cursor() -> None:
        """Cache le curseur."""
        
    @staticmethod
    def show_cursor() -> None:
        """Affiche le curseur."""
```

## Data Models

### DisplayConfig - Configuration d'Affichage

```python
@dataclass
class DisplayConfig:
    """Configuration pour l'affichage CLI."""
    use_colors: bool = True
    verbose: bool = False
    quiet: bool = False
    show_progress: bool = True
    terminal_width: int = 80
    update_interval: float = 0.1
    animation_enabled: bool = True
```

### ProgressState - État de Progression

```python
@dataclass
class ProgressState:
    """État d'une opération en cours."""
    name: str
    current: int
    total: int
    start_time: float
    message: str = ""
    completed: bool = False
    success: bool = True
    
    @property
    def percentage(self) -> float:
        return (self.current / max(self.total, 1)) * 100
    
    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> float:
        if self.current == 0:
            return 0
        rate = self.current / self.elapsed_time
        remaining = (self.total - self.current) / rate
        return remaining
```

### ReportData - Données de Rapport

```python
@dataclass
class ReportData:
    """Données pour la génération de rapports."""
    total_sources: int
    successful_sources: int
    total_urls_found: int
    total_jobs_processed: int
    cache_hit_rate: float
    processing_time: float
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
```

## Error Handling

### Stratégie de Gestion d'Erreurs Visuelles

1. **Erreurs Critiques** : Affichage en rouge avec suggestions d'action
2. **Avertissements** : Affichage en jaune avec conseils d'optimisation
3. **Informations** : Affichage en bleu pour les notifications
4. **Succès** : Affichage en vert pour les confirmations

### Types d'Erreurs Gérées

```python
class ErrorType(Enum):
    CRITICAL = "critical"      # Arrêt du processus
    WARNING = "warning"        # Continue avec avertissement
    INFO = "info"             # Information simple
    SUCCESS = "success"        # Confirmation de succès
```

### Suggestions Automatiques

```python
ERROR_SUGGESTIONS = {
    "source_timeout": [
        "Vérifiez votre connexion internet",
        "Utilisez --sources pour exclure cette source",
        "Augmentez le timeout dans la configuration"
    ],
    "api_rate_limit": [
        "Attendez quelques minutes avant de relancer",
        "Vérifiez vos quotas API",
        "Utilisez --max-urls pour limiter les requêtes"
    ],
    "cache_error": [
        "Vérifiez que Redis est démarré",
        "Le système basculera sur FakeRedis automatiquement",
        "Consultez les logs pour plus de détails"
    ]
}
```

## Testing Strategy

### Tests d'Affichage

1. **Tests Unitaires** : Chaque composant d'affichage
2. **Tests d'Intégration** : Flux complet d'affichage
3. **Tests Visuels** : Capture d'écran automatisée
4. **Tests de Compatibilité** : Différents terminaux et tailles

### Mocks et Simulations

```python
class MockTerminal:
    """Mock du terminal pour les tests."""
    
    def __init__(self, width: int = 80, height: int = 24, supports_colors: bool = True):
        self.width = width
        self.height = height
        self.supports_colors = supports_colors
        self.output_buffer: List[str] = []
    
    def capture_output(self) -> str:
        """Capture la sortie pour validation."""
        return "\n".join(self.output_buffer)
```

## Implementation Details

### Intégration avec l'Architecture Existante

1. **Hooks dans l'Orchestrateur** : Ajout de callbacks pour les événements d'affichage
2. **Extension de l'Enhanced Logger** : Intégration avec le système d'affichage
3. **Modification Minimale de l'App** : Injection du CLIDisplay dans JinaScraperApp
4. **Compatibilité Ascendante** : Possibilité de revenir à l'ancien affichage

### Gestion des Performances

1. **Mise à Jour Throttling** : Limitation des mises à jour d'affichage
2. **Buffer d'Affichage** : Accumulation des changements avant rendu
3. **Optimisation Terminal** : Utilisation efficace des codes ANSI
4. **Mode Dégradé** : Fallback pour terminaux limités

### Configuration et Personnalisation

```python
# Configuration dans .env ou arguments CLI
CLI_DISPLAY_MODE = "modern"  # modern, classic, minimal
CLI_UPDATE_INTERVAL = 0.1    # Secondes entre mises à jour
CLI_ANIMATION_SPEED = "normal"  # slow, normal, fast
CLI_THEME = "default"        # default, dark, light, colorblind
```

### Exemples d'Affichage

#### Header de Démarrage
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🔍 JINASCRAPER v2.0                              ║
║                     Agrégateur d'Emplois IA pour le Togo                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

🚀 Initialisation du système...
[████████████████████████████████████████] 100% Configuration chargée

📊 Configuration Système:
┌─────────────────┬──────────┬─────────────────────────────────────────────────┐
│ Source          │ Statut   │ Description                                     │
├─────────────────┼──────────┼─────────────────────────────────────────────────┤
│ Emploi.tg       │ ✅ Actif  │ Source gouvernementale principale               │
│ ANPE Togo       │ ✅ Actif  │ Agence nationale pour l'emploi                 │
│ EmploiTogo.info │ ✅ Actif  │ Plateforme privée d'emploi                     │
│ YOP L-FRII      │ ✅ Actif  │ Réseau social professionnel                    │
│ LinkedIn Togo   │ ⚠️ Instable│ Timeouts fréquents                            │
│ Indeed Togo     │ ❌ Erreur │ HTTP 400 - Temporairement indisponible        │
└─────────────────┴──────────┴─────────────────────────────────────────────────┘

💾 Cache Redis: ✅ Connecté (Hit rate: 100% sur cycles précédents)
🤖 IA Services: ✅ Jina Reader + Google Gemini opérationnels
```

#### Progression en Temps Réel
```
🔍 ÉTAPE 1 - EXPLORATION DES SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 Emploi.tg          [████████████████████████████████] 100% ✅ 25 URLs trouvées
📡 ANPE Togo          [████████████████████████████████] 100% ✅ 15 URLs trouvées  
📡 EmploiTogo.info    [██████████████████████          ]  75% ⏳ 48 URLs trouvées...
📡 YOP L-FRII         [████████████████████████████████] 100% ✅ 35 URLs trouvées
📡 LinkedIn Togo      [████████                        ]  25% ⚠️ Timeout détecté
📡 Indeed Togo        [                                ]   0% ❌ HTTP 400 Error

💾 Cache: 75 URLs déjà vues (économie de 75 appels API) | ⏱️ Temps écoulé: 45s
```

#### Rapport Final
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          📊 RAPPORT DE SCRAPING                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 RÉSUMÉ EXÉCUTIF
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ Statut: SUCCÈS PARTIEL                                                   │
│ 📊 Jobs traités: 107 sur 139 URLs découvertes (77% de succès)              │
│ ⏱️ Temps total: 2m 11s                                                      │
│ 🌐 Sources actives: 4/6 (LinkedIn et Indeed temporairement indisponibles)  │
└─────────────────────────────────────────────────────────────────────────────┘

📈 PERFORMANCE PAR SOURCE
Emploi.tg       ████████████████████ 25 jobs  (100% succès)
ANPE Togo       ████████████████████ 15 jobs  (100% succès)
EmploiTogo.info ████████████████████ 64 jobs  (100% succès)
YOP L-FRII      ████████████████████ 35 jobs  (100% succès)
LinkedIn Togo   ░░░░░░░░░░░░░░░░░░░░  0 jobs  (Timeout)
Indeed Togo     ░░░░░░░░░░░░░░░░░░░░  0 jobs  (HTTP 400)

💾 EFFICACITÉ CACHE
Hit Rate: ████████████████████████████████████████ 100%
Économies: 75 appels API évités | Temps gagné: ~2m 30s

🎉 FÉLICITATIONS! Le scraping s'est terminé avec succès.
   139 nouvelles offres d'emploi découvertes pour le Togo.

📋 Actions recommandées:
   • Vérifier la connectivité LinkedIn (timeouts fréquents)
   • Contacter Indeed pour résoudre l'erreur HTTP 400
   • Relancer dans 1h pour traiter les sources manquantes

💾 Sauvegarder ce rapport? [O/n] _
```

Cette conception transformera complètement l'expérience utilisateur en passant d'une sortie technique brute à une interface moderne, informative et visuellement attrayante !

<function_calls>
<invoke name="userInput">
<parameter name="question">**Does the design look good? If so, we can move on to the implementation plan.**