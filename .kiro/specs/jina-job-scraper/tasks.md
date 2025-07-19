# Implementation Plan - Scraper d'Offres d'Emploi Jina AI + Gemini

## Vue d'Ensemble

Ce plan d'implémentation détaille les tâches nécessaires pour développer le scraper d'offres d'emploi basé sur l'architecture Jina AI + Google Gemini en deux étapes. Chaque tâche est conçue pour être exécutée de manière incrémentale, permettant des tests et validations à chaque étape.

## Tâches d'Implémentation

- [x] 1. Configuration et Infrastructure de Base

  - Créer la structure de projet Python avec les dépendances requises
  - Configurer les variables d'environnement pour les clés API Jina et Gemini
  - Mettre en place la connexion Redis pour le cache
  - Configurer la connexion Supabase pour le stockage
  - _Requirements: 3.1, 9.1, 9.3_

- [x] 2. Implémentation du Service Jina Reader

  - [ ] 2.1 Créer la classe JinaReaderService avec gestion des erreurs
    - Implémenter les méthodes d'appel API avec authentification
    - Ajouter la gestion des rate limits (5000 RPM)
    - Implémenter le retry avec backoff exponentiel
    - _Requirements: 1.1, 4.3, 7.2_


  - [x] 2.2 Configurer les paramètres pour l'Étape 1 (Exploration)


    - Implémenter la configuration "gather_all_links_at_the_end"
    - Ajouter les sélecteurs CSS pour les pages de listing
    - Créer la méthode d'extraction des URLs depuis la section "Links"
    - _Requirements: 1.1, 1.2, 1.3_




  - [x] 2.3 Configurer les paramètres pour l'Étape 2 (Analyse)


    - Implémenter la configuration ReaderLM-v2 pour la qualité maximale
    - Ajouter les sélecteurs d'exclusion (ads, sidebar, etc.)
    - Créer la méthode d'extraction de contenu Markdown propre
    - _Requirements: 2.1, 2.2, 2.3_



- [ ] 3. Implémentation du Service Gemini
  - [ ] 3.1 Créer la classe GeminiService avec Structured Output
    - Implémenter l'authentification et la configuration API
    - Définir le schéma JSON pour les offres d'emploi
    - Créer la méthode de structuration sans hallucination
    - _Requirements: 2.3, 2.4, 2.6_

  - [ ] 3.2 Optimiser les prompts pour l'extraction
    - Créer des prompts spécifiques pour chaque type de contenu
    - Implémenter la validation du JSON de sortie
    - Ajouter la gestion des erreurs de parsing
    - _Requirements: 2.5, 7.4, 10.3_

- [ ] 4. Implémentation du Cache Manager (Redis)
  - Créer la classe CacheManager pour la gestion du delta scraping
  - Implémenter les méthodes de vérification des URLs déjà traitées
  - Ajouter la gestion du TTL (7 jours) pour éviter l'accumulation
  - Créer les méthodes de nettoyage automatique du cache
  - _Requirements: 1.5, 4.1, 5.2_

- [ ] 5. Implémentation du Database Service (Supabase)
  - [ ] 5.1 Créer le schéma de base de données
    - Définir la table `jobs` avec tous les champs requis
    - Créer les index pour les performances (source_url, created_at)
    - Implémenter les contraintes d'unicité et de validation
    - _Requirements: 5.1, 5.3, 5.5_

  - [ ] 5.2 Implémenter la classe DatabaseService
    - Créer les méthodes d'upsert pour éviter les doublons
    - Implémenter la sauvegarde des métadonnées de traçabilité
    - Ajouter la gestion des offres inactives
    - _Requirements: 5.1, 5.2, 5.4_

- [ ] 6. Configuration des Sources Prioritaires du Togo
  - [ ] 6.1 Configurer emploi.tg
    - Définir l'URL de listing et les sélecteurs CSS spécifiques
    - Tester l'extraction des URLs d'offres individuelles
    - Valider l'extraction du contenu des pages de détail
    - _Requirements: 3.1, 3.2_

  - [ ] 6.2 Configurer yop.l-frii.com
    - Adapter les sélecteurs pour la structure spécifique du site
    - Gérer la pagination extensive (83+ pages)
    - Optimiser pour le contenu humanitaire/ONG
    - _Requirements: 3.1, 3.2_

  - [ ] 6.3 Configurer anpetogo.org
    - Configurer pour le jobboard officiel gouvernemental
    - Gérer le volume important (2000+ offres)
    - Adapter aux spécificités du site ANPE
    - _Requirements: 3.1, 3.2_

  - [ ] 6.4 Configurer LinkedIn Togo
    - Implémenter les sélecteurs pour les pages LinkedIn
    - Gérer les spécificités de structure LinkedIn
    - Optimiser pour la qualité internationale des offres
    - _Requirements: 3.1, 3.2_

  - [ ] 6.5 Configurer Indeed Togo
    - Adapter aux pages Indeed françaises
    - Gérer les redirections et la structure Indeed
    - Optimiser l'extraction pour ce format spécifique
    - _Requirements: 3.1, 3.2_

  - [ ] 6.6 Configurer emploitogo.info
    - Configurer pour le flux d'actualités du site
    - Gérer les offres pour candidats inscrits
    - Adapter à la structure de contenu spécifique
    - _Requirements: 3.1, 3.2_

- [ ] 7. Implémentation du Workflow Principal
  - [ ] 7.1 Créer l'orchestrateur principal (MainScraper)
    - Implémenter la logique de coordination des deux étapes
    - Créer la gestion séquentielle Étape 1 → Étape 2
    - Ajouter la gestion des erreurs globales
    - _Requirements: 4.1, 4.2, 7.1_

  - [ ] 7.2 Implémenter l'Étape 1 (Exploration)
    - Créer la méthode de traitement des pages de listing
    - Implémenter l'extraction et la validation des URLs
    - Ajouter la vérification delta avec le cache Redis
    - _Requirements: 1.1, 1.2, 1.3, 1.6_

  - [ ] 7.3 Implémenter l'Étape 2 (Analyse)
    - Créer la méthode de traitement des pages de détail
    - Implémenter l'appel séquentiel Jina Reader → Gemini
    - Ajouter la validation et la sauvegarde des données structurées
    - _Requirements: 2.1, 2.2, 2.3, 2.7_

- [ ] 8. Implémentation du Scheduler
  - Créer le système de planification pour 3 exécutions par jour
  - Implémenter les horaires fixes (08h00, 14h00, 20h00)
  - Ajouter la gestion des chevauchements et des conflits
  - Créer les mécanismes de récupération en cas d'échec
  - _Requirements: 4.1, 4.2, 4.6_

- [ ] 9. Système de Monitoring et Logging
  - [ ] 9.1 Implémenter le logging structuré
    - Créer les loggers pour chaque composant
    - Implémenter les niveaux de log appropriés
    - Ajouter la rotation et l'archivage des logs
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 9.2 Créer les métriques de performance
    - Implémenter le tracking des URLs découvertes par source
    - Ajouter les métriques de succès/échec par étape
    - Créer le suivi des coûts tokens Jina + Gemini
    - _Requirements: 6.1, 6.3, 10.6_

  - [ ] 9.3 Implémenter le système d'alertes
    - Créer les alertes pour taux d'échec élevé
    - Ajouter les notifications de dépassement de budget
    - Implémenter les alertes de sources indisponibles
    - _Requirements: 6.4, 7.1_

- [ ] 10. Optimisation des Performances et Coûts
  - [ ] 10.1 Optimiser l'utilisation de Jina Reader
    - Implémenter la sélection adaptative des paramètres
    - Optimiser les sélecteurs CSS pour réduire les tokens
    - Ajouter la logique de choix ReaderLM-v2 vs standard
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 10.2 Optimiser l'utilisation de Gemini
    - Implémenter le batch processing quand possible
    - Optimiser les prompts pour minimiser les tokens
    - Ajouter le cache des réponses pour contenus similaires
    - _Requirements: 10.3, 10.4, 10.6_

- [ ] 11. Tests et Validation
  - [ ] 11.1 Créer les tests unitaires
    - Tester chaque service individuellement avec mocks
    - Valider la gestion des erreurs et des cas limites
    - Créer les tests de validation des schémas de données
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 11.2 Implémenter les tests d'intégration
    - Tester le workflow complet Étape 1 → Étape 2
    - Valider l'intégration avec Redis et Supabase
    - Tester la gestion des erreurs en conditions réelles
    - _Requirements: 4.1, 5.1, 7.1_

  - [ ] 11.3 Effectuer les tests end-to-end
    - Tester sur un sous-ensemble de sources réelles
    - Valider la qualité des données extraites
    - Vérifier les performances et les coûts
    - _Requirements: 1.1, 2.1, 4.1_

- [ ] 12. Documentation et Déploiement
  - [ ] 12.1 Créer la documentation technique
    - Documenter l'architecture et les composants
    - Créer les guides de configuration des sources
    - Rédiger les procédures de maintenance et debugging
    - _Requirements: 9.1, 9.2_

  - [ ] 12.2 Préparer le déploiement
    - Créer les scripts de déploiement et configuration
    - Implémenter les health checks pour monitoring
    - Configurer les variables d'environnement de production
    - _Requirements: 9.3, 9.4, 9.5_

- [ ] 13. Mise en Production et Monitoring
  - Déployer le système en environnement de production
  - Configurer le monitoring et les alertes
  - Effectuer les premiers cycles de scraping supervisés
  - Ajuster les paramètres selon les performances observées
  - _Requirements: 4.1, 6.1, 6.3, 6.4_

## Notes d'Implémentation

### Priorités de Développement
1. **Phase 1** : Infrastructure de base + Services Jina/Gemini (Tâches 1-3)
2. **Phase 2** : Cache, Database et Configuration sources (Tâches 4-6)
3. **Phase 3** : Workflow principal et Scheduler (Tâches 7-8)
4. **Phase 4** : Monitoring, Optimisation et Tests (Tâches 9-11)
5. **Phase 5** : Documentation et Déploiement (Tâches 12-13)

### Considérations Techniques
- **Parallélisation** : L'Étape 1 peut traiter les sources en parallèle
- **Rate Limiting** : Respecter strictement les limites Jina (5000 RPM)
- **Gestion Mémoire** : Traiter les offres par batch pour éviter la surcharge
- **Monitoring** : Surveiller les coûts tokens en temps réel

### Critères de Succès
- **Fonctionnel** : 3 cycles par jour sans interruption
- **Performance** : >90% de taux de succès d'extraction
- **Qualité** : >95% de complétude des champs essentiels
- **Coût** : Respect du budget tokens défini