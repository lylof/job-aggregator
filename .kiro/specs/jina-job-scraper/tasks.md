# Implementation Plan - Scraper d'Offres d'Emploi Jina AI + Gemini

## Vue d'Ensemble

Ce plan d'implémentation détaille les tâches nécessaires pour développer le scraper d'offres d'emploi basé sur l'architecture Jina AI + Google Gemini en deux étapes. Chaque tâche est conçue pour être exécutée de manière incrémentale, permettant des tests et validations à chaque étape.

## Tâches d'Implémentation

- [x] 1. Mise en place de l'architecture de configuration robuste

  - [x] 1.1 Créer la structure de fichiers de configuration
    - Créer le dossier `jinascraper/config/` avec `base_config.py`
    - Créer le dossier `jinascraper/config/sources/` pour les configurations spécifiques
    - Créer `jinascraper/config/source_registry.py` pour le registre central
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
    
  - [x] 1.2 Implémenter la configuration de base
    - Créer la classe `JinaReaderBaseConfig` avec les paramètres par défaut
    - Créer la classe `SourceBaseConfig` avec mécanisme de fusion
    - Implémenter les méthodes de validation de configuration
    - _Requirements: 3.2, 9.1, 9.3_
    
  - [x] 1.3 Implémenter les configurations spécifiques par source
    - Créer un fichier de configuration pour chaque source
    - Définir les paramètres spécifiques à chaque source
    - Implémenter les patterns d'extraction d'URL spécifiques
    - _Requirements: 3.2, 3.3, 3.4_
    
  - [x] 1.4 Implémenter le registre central des sources
    - Créer la classe `SourceRegistry` pour accéder aux sources
    - Implémenter les méthodes pour récupérer les sources par nom, type, etc.
    - Ajouter la fusion explicite des paramètres de base et spécifiques
    - _Requirements: 3.1, 3.3, 3.5_
    
  - [x] 1.5 Implémenter les nettoyeurs d'URL spécifiques
    - Créer le dossier `jinascraper/services/url_cleaners/`
    - Créer un fichier de nettoyage pour chaque source
    - Implémenter la façade `url_cleaner.py` qui délègue aux nettoyeurs spécifiques
    - _Requirements: 3.3, 7.4_

- [x] 2. Configuration et Infrastructure de Base
  - [x] 2.1 Créer la structure de projet Python avec les dépendances requises
    - Mettre à jour `requirements.txt` avec les dépendances nécessaires
    - Configurer l'environnement de développement
    - Créer la structure de base du projet
    - _Requirements: 9.1, 9.3_
    
  - [x] 2.2 Configurer les variables d'environnement
    - Créer le fichier `.env.example` avec les variables nécessaires
    - Implémenter le chargement des variables d'environnement
    - Valider les variables d'environnement au démarrage
    - _Requirements: 9.1, 9.3_
    
  - [x] 2.3 Mettre en place la configuration Redis pour le cache
    - Configurer la connexion Redis
    - Implémenter les méthodes de base pour le cache
    - Tester la connexion Redis
    - _Requirements: 5.2_
    
  - [x] 2.4 Configurer la connexion Supabase pour le stockage
    - Configurer la connexion Supabase
    - Implémenter les méthodes de base pour le stockage
    - Tester la connexion Supabase
    - _Requirements: 5.1, 5.3_

- [x] 3. Implémentation du Service Jina Reader
  - [x] 3.1 Créer la classe JinaClient avec gestion des erreurs
    - Implémenter les méthodes d'appel API avec authentification
    - Ajouter la gestion des rate limits (5000 RPM)
    - Implémenter le retry avec backoff exponentiel
    - _Requirements: 1.1, 4.3, 7.2_

  - [x] 3.2 Configurer les paramètres pour l'Étape 1 (Exploration)
    - Implémenter la configuration "gather_all_links_at_the_end"
    - Ajouter les sélecteurs CSS pour les pages de listing
    - Créer la méthode d'extraction des URLs depuis la section "Links"
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.3 Configurer les paramètres pour l'Étape 2 (Analyse)
    - Implémenter la configuration ReaderLM-v2 pour la qualité maximale
    - Ajouter les sélecteurs d'exclusion (ads, sidebar, etc.)
    - Créer la méthode d'extraction de contenu Markdown propre
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Implémentation du Service Gemini
  - [x] 4.1 Créer la classe GeminiService avec Structured Output
    - Implémenter l'authentification et la configuration API
    - Définir le schéma JSON pour les offres d'emploi
    - Créer la méthode de structuration sans hallucination
    - _Requirements: 2.3, 2.4, 2.6_

  - [x] 4.2 Optimiser les prompts pour l'extraction
    - Créer des prompts spécifiques pour chaque type de contenu
    - Implémenter la validation du JSON de sortie
    - Ajouter la gestion des erreurs de parsing
    - _Requirements: 2.5, 7.4, 10.3_

- [x] 5. Implémentation du Cache Manager (Redis)
  - [x] 5.1 Créer la classe CacheManager pour la gestion du delta scraping
    - Implémenter les méthodes de vérification des URLs déjà traitées
    - Ajouter la gestion du TTL (7 jours) pour éviter l'accumulation
    - Créer les méthodes de nettoyage automatique du cache
    - _Requirements: 1.5, 4.1, 5.2_

- [x] 6. Implémentation du Database Service (Supabase)
  - [x] 6.1 Créer le schéma de base de données
    - Définir la table `jobs` avec tous les champs requis
    - Créer les index pour les performances (source_url, created_at)
    - Implémenter les contraintes d'unicité et de validation
    - _Requirements: 5.1, 5.3, 5.5_

  - [x] 6.2 Implémenter la classe DatabaseService
    - Créer les méthodes d'upsert pour éviter les doublons
    - Implémenter la sauvegarde des métadonnées de traçabilité
    - Ajouter la gestion des offres inactives
    - _Requirements: 5.1, 5.2, 5.4_

- [x] 7. Implémentation des Sources Prioritaires du Togo
  - [x] 7.1 Implémenter emploi.tg
    - Créer la configuration spécifique dans `config/sources/emploi_tg.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/emploi_tg_cleaner.py`
    - Tester l'extraction des URLs d'offres individuelles
    - _Requirements: 3.1, 3.2_

  - [x] 7.2 Implémenter yop.l-frii.com
    - Créer la configuration spécifique dans `config/sources/yop_lfrii.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/yop_lfrii_cleaner.py`
    - Gérer la pagination extensive (83+ pages)
    - _Requirements: 3.1, 3.2_

  - [x] 7.3 Implémenter anpetogo.org
    - Créer la configuration spécifique dans `config/sources/anpetogo.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/anpetogo_cleaner.py`
    - Adapter aux spécificités du site ANPE
    - _Requirements: 3.1, 3.2_

  - [x] 7.4 Implémenter LinkedIn Togo
    - Créer la configuration spécifique dans `config/sources/linkedin_togo.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/linkedin_togo_cleaner.py`
    - Gérer les spécificités de structure LinkedIn
    - _Requirements: 3.1, 3.2_

  - [x] 7.5 Implémenter Indeed Togo
    - Créer la configuration spécifique dans `config/sources/indeed_togo.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/indeed_togo_cleaner.py`
    - Gérer les redirections et la structure Indeed
    - _Requirements: 3.1, 3.2_

  - [x] 7.6 Implémenter emploitogo.info
    - Créer la configuration spécifique dans `config/sources/emploitogo_info.py`
    - Implémenter le nettoyeur d'URL dans `services/url_cleaners/emploitogo_info_cleaner.py`
    - Adapter à la structure de contenu spécifique
    - _Requirements: 3.1, 3.2_

- [x] 8. Implémentation du Workflow Principal
  - [x] 8.1 Créer l'orchestrateur principal (ScrapingOrchestrator)
    - Implémenter la classe ScrapingOrchestrator dans jinascraper/core/orchestrator.py
    - Créer la logique de coordination des deux étapes
    - Ajouter la gestion séquentielle Étape 1 → Étape 2
    - Implémenter la gestion des erreurs globales et la récupération
    - _Requirements: 4.1, 4.2, 7.1_

  - [x] 8.2 Implémenter l'Étape 1 (Exploration)
    - Créer la méthode run_stage1_exploration() dans l'orchestrateur
    - Implémenter l'extraction et la validation des URLs pour toutes les sources
    - Ajouter la vérification delta avec le cache Redis
    - Intégrer la gestion du parallélisme avec rate limiting
    - _Requirements: 1.1, 1.2, 1.3, 1.6_

  - [x] 8.3 Implémenter l'Étape 2 (Analyse)
    - Créer la méthode run_stage2_analysis() dans l'orchestrateur
    - Implémenter l'appel séquentiel Jina Reader → Gemini pour chaque URL
    - Ajouter la validation et la sauvegarde des données structurées
    - Intégrer la gestion des batches pour optimiser les performances
    - _Requirements: 2.1, 2.2, 2.3, 2.7_

- [x] 9. Implémentation du Point d'Entrée Principal
  - [x] 9.1 Créer le script principal main.py
    - Implémenter le point d'entrée avec gestion des arguments CLI
    - Ajouter les modes d'exécution (single run, scheduler, test)
    - Créer la configuration du logging et de l'environnement
    - _Requirements: 9.1, 9.3_

  - [ ] 9.2 Implémenter le Scheduler
    - Créer la classe Scheduler dans jinascraper/core/scheduler.py
    - Implémenter les horaires fixes (08h00, 14h00, 20h00)
    - Ajouter la gestion des chevauchements et des conflits
    - Créer les mécanismes de récupération en cas d'échec
    - _Requirements: 4.1, 4.2, 4.6_

- [ ] 10. Système de Monitoring et Logging
  - [x] 10.1 Implémenter le logging structuré
    - Configurer structlog dans main.py
    - Implémenter les loggers pour chaque composant avec contexte
    - Configurer les niveaux de log par environnement
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 10.2 Créer les métriques de performance
    - Implémenter la classe MetricsCollector dans jinascraper/core/metrics.py
    - Ajouter le tracking des URLs découvertes par source
    - Créer les métriques de succès/échec par étape
    - Implémenter le suivi des coûts tokens Jina + Gemini
    - _Requirements: 6.1, 6.3, 10.6_

  - [ ] 10.3 Implémenter le système d'alertes
    - Créer la classe AlertManager dans jinascraper/core/alerts.py
    - Implémenter les alertes pour taux d'échec élevé
    - Ajouter les notifications de dépassement de budget
    - Créer les alertes de sources indisponibles
    - _Requirements: 6.4, 7.1_

- [ ] 11. API et Interface de Consultation
  - [ ] 11.1 Créer l'API REST avec FastAPI
    - Implémenter jinascraper/api/main.py avec FastAPI
    - Créer les endpoints pour consultation des offres (/jobs, /jobs/{id})
    - Ajouter la pagination et le filtrage par critères
    - Implémenter les métadonnées de fraîcheur et source
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [ ] 11.2 Créer les modèles de réponse API
    - Implémenter les schémas Pydantic pour les réponses API
    - Ajouter la validation des paramètres de requête
    - Créer les modèles de pagination et filtrage
    - _Requirements: 8.1, 8.4_

- [ ] 12. Optimisation des Performances et Coûts
  - [ ] 12.1 Optimiser l'utilisation de Jina Reader
    - Améliorer la sélection adaptative des paramètres dans JinaClient
    - Optimiser les sélecteurs CSS pour réduire les tokens
    - Affiner la logique de choix ReaderLM-v2 vs standard
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 12.2 Optimiser l'utilisation de Gemini
    - Améliorer le batch processing dans GeminiService
    - Optimiser davantage les prompts pour minimiser les tokens
    - Ajouter le cache des réponses pour contenus similaires
    - _Requirements: 10.3, 10.4, 10.6_

- [ ] 13. Tests et Validation
  - [x] 13.1 Créer les tests unitaires de base
    - Implémenter les tests pour la configuration et le registre des sources
    - Créer les tests pour les nettoyeurs d'URL
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 13.2 Implémenter les tests d'intégration
    - Créer jinascraper/tests/test_integration.py pour le workflow complet
    - Tester l'intégration Étape 1 → Étape 2 → Storage
    - Valider l'intégration avec Redis et Supabase
    - Tester la gestion des erreurs en conditions réelles
    - _Requirements: 4.1, 5.1, 7.1_

  - [ ] 13.3 Effectuer les tests end-to-end
    - Créer jinascraper/tests/test_e2e.py pour les tests complets
    - Tester sur un sous-ensemble de sources réelles
    - Valider la qualité des données extraites
    - Vérifier les performances et les coûts
    - _Requirements: 1.1, 2.1, 4.1_

- [ ] 14. Documentation et Déploiement
  - [x] 14.1 Créer la documentation de base
    - Rédiger README.md avec guide d'installation et utilisation
    - _Requirements: 9.1, 9.2_

  - [ ] 14.2 Compléter la documentation technique
    - Documenter l'architecture dans docs/architecture.md
    - Créer docs/sources-configuration.md pour la configuration des sources
    - Rédiger docs/troubleshooting.md pour le debugging
    - _Requirements: 9.1, 9.2_

  - [ ] 14.3 Préparer le déploiement
    - Créer docker-compose.yml pour l'environnement de développement
    - Implémenter les health checks dans l'API
    - Créer les scripts de déploiement deploy/
    - Configurer les variables d'environnement de production
    - _Requirements: 9.3, 9.4, 9.5_

- [ ] 15. Mise en Production et Monitoring
  - [ ] 15.1 Déploiement initial
    - Déployer le système en environnement de production
    - Configurer le monitoring et les alertes
    - Effectuer les premiers cycles de scraping supervisés
    - _Requirements: 4.1, 6.1, 6.3_

  - [ ] 15.2 Optimisation post-déploiement
    - Ajuster les paramètres selon les performances observées
    - Optimiser les coûts API basés sur l'usage réel
    - Affiner les sélecteurs CSS selon les résultats
    - _Requirements: 6.4, 10.1, 10.2_

## Notes d'Implémentation

### Priorités de Développement
1. **Phase 0** : Architecture de configuration robuste (Tâche 1) ✅
2. **Phase 1** : Infrastructure de base + Services Jina/Gemini (Tâches 2-4) ✅
3. **Phase 2** : Cache, Database et Configuration sources (Tâches 5-7) ✅
4. **Phase 3** : Workflow principal et Scheduler (Tâches 8-9) ✅ (Scheduler restant)
5. **Phase 4** : Monitoring, Optimisation et Tests (Tâches 10-13) 🔄
6. **Phase 5** : Documentation et Déploiement (Tâches 14-15) 🔄

### Considérations Techniques
- **Isolation des sources** : Garantir qu'une modification pour une source n'affecte jamais les autres
- **Parallélisation** : L'Étape 1 peut traiter les sources en parallèle
- **Rate Limiting** : Respecter strictement les limites Jina (5000 RPM)
- **Gestion Mémoire** : Traiter les offres par batch pour éviter la surcharge
- **Monitoring** : Surveiller les coûts tokens en temps réel

### Critères de Succès
- **Fonctionnel** : 3 cycles par jour sans interruption
- **Performance** : >90% de taux de succès d'extraction
- **Qualité** : >95% de complétude des champs essentiels
- **Coût** : Respect du budget tokens défini
- **Robustesse** : Aucune régression entre sources lors des modifications