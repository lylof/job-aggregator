# Requirements Document - Scraper d'Offres d'Emploi avec Jina AI + Gemini

## Introduction

Ce projet vise à créer un scraper d'offres d'emploi moderne et efficace utilisant une architecture hybride Jina AI + Google Gemini. L'objectif est de maximiser la qualité des données extraites en combinant les forces de Jina Reader (extraction de contenu web propre) et de Gemini (structuration intelligente sans hallucination).

Le système est conçu autour d'un scraping en deux étapes pour maximiser la qualité des données :
- **Étape 1 (Exploration - Page de Liste) :** Parcourir les pages de listing d'offres d'emploi pour identifier et extraire les URLs uniques de chaque offre individuelle
- **Étape 2 (Analyse - Page de Détail) :** Pour chaque URL de détail non présente en base, visiter la page et extraire un ensemble complet d'informations structurées

Cette approche garantit la crédibilité des données en extrayant uniquement ce qui est publié, sans enrichissement artificiel.

## Requirements

### Requirement 1 - Étape 1 : Exploration des Pages de Listing (Jina Reader)

**User Story:** En tant que système d'exploration, je veux parcourir les pages de listing d'offres d'emploi pour extraire uniquement les URLs des offres individuelles, afin d'optimiser le processus de découverte.

#### Acceptance Criteria

1. WHEN le système traite une page de listing THEN il SHALL utiliser Jina Reader avec le paramètre "gather_all_links_at_the_end=true"
2. WHEN Jina Reader traite la page THEN il SHALL créer automatiquement une section "Buttons & Links" contenant toutes les URLs
3. WHEN les URLs sont extraites THEN le système SHALL filtrer uniquement les liens vers les pages d'offres individuelles
4. WHEN une URL d'offre est identifiée THEN le système SHALL vérifier si elle existe déjà en base de données
5. IF une URL est déjà connue THEN le système SHALL l'ignorer (delta scraping)
6. WHEN l'exploration est terminée THEN le système SHALL retourner une liste d'URLs nouvelles à traiter

### Requirement 2 - Étape 2 : Analyse des Pages de Détail (Jina Reader + Gemini)

**User Story:** En tant que système d'analyse, je veux extraire et structurer toutes les informations disponibles de chaque offre d'emploi, afin de créer une base de données complète et fiable.

#### Acceptance Criteria

1. WHEN le système traite une URL d'offre individuelle THEN il SHALL utiliser Jina Reader avec ReaderLM-v2 pour une extraction de qualité maximale
2. WHEN le contenu est extrait par Jina THEN il SHALL être au format Markdown propre et structuré
3. WHEN le contenu Markdown est obtenu THEN le système SHALL l'envoyer à Gemini avec un schéma de structured output
4. WHEN Gemini traite le contenu THEN il SHALL extraire et structurer les informations sans hallucination ni enrichissement
5. WHEN les données sont structurées THEN elles SHALL inclure tous les champs disponibles : titre, entreprise, description complète, salaire, lieu, contact, etc.
6. IF certaines informations ne sont pas présentes THEN Gemini SHALL laisser les champs vides plutôt que d'inventer
7. WHEN la structuration est terminée THEN le système SHALL valider le JSON de sortie contre le schéma défini

### Requirement 3 - Gestion des Sources Prioritaires du Togo

**User Story:** En tant qu'administrateur système, je veux configurer et gérer les 6 sources prioritaires d'offres d'emploi du Togo, afin d'assurer une couverture complète du marché local.

#### Acceptance Criteria

1. WHEN le système démarre THEN il SHALL charger la configuration des 6 sources prioritaires : emploi.tg, emploitogo.info, yop.l-frii.com, anpetogo.org, LinkedIn Togo, Indeed Togo
2. WHEN une source est configurée THEN elle SHALL inclure l'URL de listing, les sélecteurs CSS spécifiques et les paramètres Jina Reader optimisés
3. WHEN le système traite une source THEN il SHALL appliquer la configuration spécifique à cette source
4. WHEN une source change sa structure THEN l'administrateur SHALL pouvoir mettre à jour la configuration sans redéploiement
5. IF une source devient indisponible THEN le système SHALL continuer avec les autres sources et logger l'incident
6. WHEN toutes les sources sont traitées THEN le système SHALL produire un rapport de couverture par source

### Requirement 4 - Planification et Exécution Cyclique

**User Story:** En tant que système automatisé, je veux exécuter le scraping 3 fois par jour (08h, 14h, 20h) pour maintenir les données à jour, afin d'assurer la fraîcheur des offres d'emploi.

#### Acceptance Criteria

1. WHEN le système est planifié THEN il SHALL s'exécuter automatiquement à 08h00, 14h00 et 20h00 chaque jour
2. WHEN un cycle de scraping démarre THEN il SHALL traiter séquentiellement l'Étape 1 puis l'Étape 2
3. WHEN l'Étape 1 est exécutée THEN le système SHALL traiter toutes les sources en parallèle avec respect du rate limiting Jina (5000 RPM)
4. WHEN l'Étape 2 est exécutée THEN le système SHALL traiter les nouvelles URLs par batch pour optimiser les appels Gemini
5. WHEN un cycle est terminé THEN le système SHALL enregistrer les métriques et préparer le cycle suivant
6. IF un cycle échoue THEN le système SHALL logger l'erreur et continuer avec le cycle suivant planifié

### Requirement 5 - Stockage et Persistance des Données

**User Story:** En tant que système de données, je veux stocker les offres d'emploi extraites de manière structurée et efficace, afin de permettre des requêtes rapides et une analyse des données.

#### Acceptance Criteria

1. WHEN une offre est extraite avec succès THEN le système SHALL la stocker dans une base de données avec un schéma normalisé
2. WHEN une offre existe déjà THEN le système SHALL effectuer un upsert pour mettre à jour les informations
3. WHEN les données sont stockées THEN elles SHALL inclure des métadonnées de traçabilité (source, date d'extraction, version)
4. IF une offre n'est plus disponible THEN le système SHALL marquer l'offre comme inactive plutôt que de la supprimer
5. WHEN les données sont persistées THEN le système SHALL maintenir un index pour les recherches rapides

### Requirement 6 - Monitoring et Observabilité

**User Story:** En tant qu'opérateur système, je veux surveiller la santé et les performances du scraper, afin de détecter et résoudre rapidement les problèmes.

#### Acceptance Criteria

1. WHEN le système s'exécute THEN il SHALL générer des logs structurés avec différents niveaux de détail
2. WHEN une erreur survient THEN le système SHALL logger l'erreur avec le contexte complet pour le debugging
3. WHEN un cycle de scraping est terminé THEN le système SHALL produire un rapport de synthèse
4. IF des anomalies sont détectées THEN le système SHALL envoyer des alertes configurables
5. WHEN les métriques sont collectées THEN elles SHALL être exportables vers des systèmes de monitoring externes

### Requirement 7 - Gestion des Erreurs et Résilience

**User Story:** En tant que système robuste, je veux gérer gracieusement les erreurs et les situations exceptionnelles, afin de maintenir un service fiable même en cas de problèmes.

#### Acceptance Criteria

1. WHEN Jina Reader retourne une erreur 4xx THEN le système SHALL logger l'erreur et passer à l'URL suivante
2. WHEN Jina Reader retourne une erreur 5xx THEN le système SHALL implémenter une stratégie de retry
3. WHEN une source devient indisponible THEN le système SHALL continuer avec les autres sources
4. IF le parsing d'une offre échoue THEN le système SHALL sauvegarder le contenu brut pour analyse manuelle
5. WHEN des erreurs critiques surviennent THEN le système SHALL maintenir un état cohérent et permettre une reprise

### Requirement 8 - API et Interface de Consultation

**User Story:** En tant qu'utilisateur final ou système client, je veux accéder aux offres d'emploi extraites via une API simple et efficace, afin d'intégrer ces données dans d'autres applications.

#### Acceptance Criteria

1. WHEN un client fait une requête API THEN le système SHALL retourner les offres dans un format JSON standardisé
2. WHEN les offres sont nombreuses THEN l'API SHALL supporter la pagination avec des paramètres configurables
3. WHEN un client recherche des offres THEN l'API SHALL supporter le filtrage par critères multiples
4. IF un client demande une offre spécifique THEN l'API SHALL retourner tous les détails disponibles
5. WHEN l'API est utilisée THEN elle SHALL inclure des métadonnées sur la fraîcheur et la source des données

### Requirement 9 - Configuration et Déploiement

**User Story:** En tant que DevOps, je veux déployer et configurer facilement le scraper dans différents environnements, afin de maintenir une infrastructure flexible et maintenable.

#### Acceptance Criteria

1. WHEN le système est déployé THEN il SHALL utiliser des variables d'environnement pour la configuration sensible
2. WHEN la configuration change THEN le système SHALL pouvoir recharger la configuration sans redémarrage
3. WHEN le système démarre THEN il SHALL valider toute la configuration avant de commencer le traitement
4. IF des dépendances externes sont indisponibles THEN le système SHALL échouer de manière explicite au démarrage
5. WHEN le système est en production THEN il SHALL supporter les health checks pour les orchestrateurs

### Requirement 10 - Optimisation des Coûts API (Jina + Gemini)

**User Story:** En tant que gestionnaire de budget, je veux optimiser l'utilisation des tokens Jina AI et Gemini, afin de maintenir les coûts opérationnels sous contrôle tout en maximisant la qualité des données.

#### Acceptance Criteria

1. WHEN le système utilise Jina Reader pour l'Étape 1 THEN il SHALL utiliser des paramètres optimisés pour l'extraction de liens uniquement
2. WHEN le système utilise Jina Reader pour l'Étape 2 THEN il SHALL utiliser ReaderLM-v2 seulement pour les pages complexes
3. WHEN le système utilise Gemini THEN il SHALL optimiser les prompts pour minimiser les tokens d'entrée et de sortie
4. WHEN les données sont structurées THEN Gemini SHALL utiliser le mode "structured output" pour éviter les tokens inutiles
5. IF le budget de tokens est atteint THEN le système SHALL implémenter une stratégie de priorisation par source
6. WHEN les coûts sont calculés THEN le système SHALL fournir des rapports détaillés d'utilisation Jina + Gemini