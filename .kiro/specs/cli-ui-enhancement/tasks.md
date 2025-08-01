# Implementation Plan - Amélioration Interface CLI JinaScraper

## Vue d'ensemble

Ce plan d'implémentation transforme l'interface CLI technique actuelle en une expérience utilisateur moderne et esthétique. Chaque tâche est conçue pour être exécutée de manière incrémentale, en maintenant la compatibilité avec l'architecture existante.

## Tâches d'Implémentation

- [x] 1. Créer les utilitaires de base pour l'affichage terminal




  - Implémenter `jinascraper/utils/terminal_utils.py` avec détection de taille, couleurs et contrôles curseur
  - Créer les fonctions de base : `get_terminal_size()`, `supports_colors()`, `clear_line()`, `move_cursor_up()`
  - Ajouter la gestion des codes ANSI pour le positionnement et les couleurs
  - Implémenter la détection automatique des capacités du terminal

  - _Requirements: 6.4, 6.5_





- [x] 2. Développer le système de barres de progression

  - Créer `jinascraper/utils/progress_manager.py` avec la classe `ProgressManager`
  - Implémenter `ProgressBar` avec rendu ASCII personnalisable
  - Ajouter le support des barres multiples simultanées avec mise à jour en temps réel

  - Créer les méthodes `create_progress_bar()`, `update_progress_bar()`, `complete_progress_bar()`
  - Implémenter le calcul automatique du temps restant et de la vitesse
  - _Requirements: 2.1, 2.2, 2.3, 7.1_


- [x] 3. Implémenter le générateur de rapports visuels

  - Créer `jinascraper/utils/report_generator.py` avec la classe `ReportGenerator`
  - Développer `generate_startup_report()` avec header ASCII et tableau de sources

  - Implémenter `generate_final_report()` avec graphiques ASCII et métriques visuelles
  - Créer `create_ascii_chart()` pour les graphiques en barres textuelles



  - Ajouter `create_status_table()` pour les tableaux formatés avec bordures
  - _Requirements: 4.1, 4.2, 4.3, 7.5_






- [ ] 4. Créer le gestionnaire d'affichage principal
  - Développer `jinascraper/utils/cli_display.py` avec la classe `CLIDisplay`

  - Implémenter `show_startup_header()` avec logo ASCII JinaScraper
  - Créer `show_configuration_summary()` avec tableau des sources et leur statut
  - Développer `show_stage_header()` avec séparateurs visuels pour Stage 1/2



  - Ajouter `update_progress()` pour les mises à jour temps réel par source
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1_

- [ ] 5. Intégrer la gestion d'erreurs élégante
  - Étendre `CLIDisplay` avec `show_error()` pour affichage d'erreurs formatées
  - Créer un système de suggestions automatiques basé sur le type d'erreur
  - Implémenter les niveaux d'erreur visuels (critical, warning, info, success)
  - Ajouter `show_cache_stats()` pour les statistiques Redis avec indicateurs visuels
  - Développer la gestion des notifications non-intrusives
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.1, 9.2_

- [ ] 6. Créer les modèles de données pour l'affichage
  - Implémenter `DisplayConfig` dataclass dans `cli_display.py`
  - Créer `ProgressState` dataclass avec calculs automatiques de pourcentage et temps
  - Développer `ReportData` dataclass pour structurer les données de rapport
  - Ajouter les propriétés calculées pour `percentage`, `elapsed_time`, `estimated_remaining`
  - Créer les enums pour `ErrorType` et `DisplayMode`
  - _Requirements: 6.1, 6.2, 7.1, 7.2_

- [ ] 7. Intégrer l'affichage moderne dans l'application principale
  - Modifier `jinascraper/app.py` pour intégrer `CLIDisplay`
  - Remplacer l'enhanced_logger basique par le nouveau système d'affichage
  - Ajouter l'initialisation de `CLIDisplay` dans `JinaScraperApp.__init__()`
  - Modifier `run_full_scrape()` pour utiliser les nouveaux hooks d'affichage
  - Maintenir la compatibilité avec les options existantes (--verbose, --quiet, --no-color)
  - _Requirements: 1.1, 3.2, 6.1, 6.2, 6.3_

- [ ] 8. Ajouter les hooks d'affichage dans l'orchestrateur
  - Modifier `jinascraper/core/orchestrator.py` pour ajouter des callbacks d'affichage
  - Créer `set_display_callback()` pour recevoir l'instance CLIDisplay
  - Ajouter les hooks dans `run_stage1_exploration()` pour les mises à jour de progression
  - Intégrer les hooks dans `run_stage2_analysis()` pour le suivi temps réel
  - Implémenter les notifications de cache hits et statistiques
  - _Requirements: 2.2, 2.3, 2.4, 7.3, 9.3_

- [ ] 9. Développer le système de notifications intelligentes
  - Étendre `CLIDisplay` avec `show_notification()` pour les alertes contextuelles
  - Implémenter la détection automatique des événements notifiables
  - Créer les notifications pour : nouvelles URLs, cache efficace, sources indisponibles
  - Ajouter les messages de félicitation pour les succès et optimisations
  - Développer les explications automatiques pour les délais inattendus
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 10. Implémenter les fonctionnalités d'export et sauvegarde
  - Créer `export_report()` dans `ReportGenerator` avec support JSON, HTML, texte
  - Ajouter les options d'export dans le rapport final avec interface interactive
  - Implémenter `generate_diagnostic_report()` pour les rapports d'erreur détaillés
  - Créer la sauvegarde automatique des logs avec horodatage
  - Ajouter la gestion du clipboard pour copie rapide des résultats
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 11. Créer les tests pour les composants d'affichage
  - Développer `test_cli_display.py` avec tests unitaires pour CLIDisplay
  - Créer `test_progress_manager.py` pour valider les barres de progression
  - Implémenter `test_report_generator.py` pour les rapports et graphiques
  - Ajouter `MockTerminal` pour simuler différents environnements de terminal
  - Créer les tests d'intégration pour le workflow complet d'affichage
  - _Requirements: Validation de tous les requirements_

- [ ] 12. Optimiser les performances d'affichage
  - Implémenter le throttling des mises à jour dans `ProgressManager`
  - Créer un buffer d'affichage pour accumuler les changements avant rendu
  - Ajouter la détection de performance pour adapter la fréquence de mise à jour
  - Optimiser l'utilisation des codes ANSI pour minimiser les redraws
  - Implémenter le mode dégradé pour les terminaux avec limitations
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 13. Ajouter la configuration et personnalisation
  - Créer les variables d'environnement pour `CLI_DISPLAY_MODE`, `CLI_THEME`, `CLI_UPDATE_INTERVAL`
  - Implémenter la détection automatique des préférences utilisateur
  - Ajouter le support des thèmes (default, dark, light, colorblind)
  - Créer la configuration adaptative selon la taille du terminal
  - Développer les profils de performance (slow, normal, fast)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 14. Intégrer les fonctionnalités interactives
  - Ajouter la gestion des touches pendant l'exécution (s=stats, p=pause, h=help)
  - Implémenter `handle_user_input()` avec écoute non-bloquante du clavier
  - Créer les menus contextuels pour les options avancées
  - Ajouter la confirmation interactive pour l'arrêt (Ctrl+C)
  - Développer l'aide contextuelle accessible via 'h'
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 15. Finaliser l'intégration et les tests de régression
  - Valider la compatibilité avec toutes les options CLI existantes
  - Tester l'affichage sur différents terminaux (Windows CMD, PowerShell, Unix)
  - Vérifier les performances avec de gros volumes de données
  - Créer les tests de régression pour s'assurer qu'aucune fonctionnalité existante n'est cassée
  - Documenter les nouvelles fonctionnalités dans le guide CLI
  - _Requirements: Validation complète de tous les requirements_

## Notes d'Implémentation

### Priorités de Développement
1. **Phase 1** (Tâches 1-6) : Fondations et composants de base
2. **Phase 2** (Tâches 7-10) : Intégration avec l'architecture existante
3. **Phase 3** (Tâches 11-15) : Tests, optimisations et finalisation

### Compatibilité
- Maintenir la compatibilité avec toutes les options CLI existantes
- Possibilité de revenir à l'ancien affichage via variable d'environnement
- Support des terminaux limités avec mode dégradé automatique

### Performance
- Throttling des mises à jour pour éviter le scintillement
- Buffer d'affichage pour optimiser les rendus
- Détection automatique des capacités du terminal

### Tests
- Tests unitaires pour chaque composant
- Tests d'intégration pour le workflow complet
- Tests de compatibilité sur différents environnements
- Validation de régression pour l'architecture existante