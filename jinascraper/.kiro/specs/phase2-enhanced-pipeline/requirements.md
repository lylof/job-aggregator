# Requirements Document - Phase 2: Enhanced Data Pipeline

## Introduction

Cette spec définit l'implémentation de la Phase 2 du projet jinascraper : l'enrichissement du pipeline de données avec extraction Markdown + structuration JSON avancée. L'objectif est d'étendre l'architecture existante sans casser le code en place, en ajoutant des capacités d'extraction de données de qualité industrielle.

## Requirements

### Requirement 1: Extension Configuration Sources pour Stage 2

**User Story:** En tant que développeur, je veux pouvoir configurer des paramètres spécialisés pour l'Étape 2 par source, afin d'optimiser l'extraction de contenu sans impacter l'Étape 1 existante.

#### Acceptance Criteria

1. WHEN une source est configurée THEN elle SHALL pouvoir avoir des paramètres stage2_params optionnels
2. WHEN stage2_params n'est pas défini THEN le système SHALL utiliser un fallback intelligent basé sur la config existante
3. WHEN stage2_params est défini THEN il SHALL contenir des paramètres Jina Reader optimisés pour l'extraction détaillée
4. IF une source n'a pas de stage2_params THEN l'Étape 2 SHALL continuer de fonctionner avec les paramètres par défaut
5. WHEN la configuration est modifiée THEN elle SHALL être rétrocompatible avec le code existant

### Requirement 2: Extension Base de Données pour Données Enrichies

**User Story:** En tant que système de stockage, je veux pouvoir stocker les données enrichies de l'Étape 2 sans impacter les données existantes, afin de préserver la compatibilité et les performances.

#### Acceptance Criteria

1. WHEN la base de données est étendue THEN elle SHALL ajouter des colonnes optionnelles (NULL par défaut)
2. WHEN des données Stage 2 sont stockées THEN elles SHALL inclure raw_content_markdown et structured_data_json
3. WHEN des requêtes existantes sont exécutées THEN elles SHALL continuer de fonctionner sans modification
4. IF une migration échoue THEN elle SHALL être facilement réversible (DROP COLUMN)
5. WHEN des données sont stockées THEN le processing_stage SHALL indiquer 'stage1' ou 'stage2'

### Requirement 3: Service Enhanced Detail Scraper

**User Story:** En tant que système d'extraction, je veux un nouveau service d'extraction enrichie qui produit du Markdown propre et du JSON structuré, afin d'améliorer la qualité des données sans modifier les services existants.

#### Acceptance Criteria

1. WHEN le service est appelé THEN il SHALL extraire le contenu Markdown avec des paramètres optimisés par source
2. WHEN le contenu Markdown est obtenu THEN il SHALL être nettoyé avec css_selector_only pour isoler le contenu principal
3. WHEN le Markdown est traité THEN il SHALL être envoyé à Gemini pour structuration JSON avancée
4. IF l'extraction échoue THEN le système SHALL logger l'erreur et continuer sans impacter l'Étape 1
5. WHEN l'extraction réussit THEN elle SHALL retourner un objet avec raw_content_markdown et structured_data_json

### Requirement 4: Prompt Gemini Expert pour Structuration Avancée

**User Story:** En tant que système d'IA, je veux un prompt Gemini spécialisé qui extrait des données structurées riches à partir du Markdown, afin de produire des données d'emploi de haute qualité.

#### Acceptance Criteria

1. WHEN le prompt est utilisé THEN il SHALL extraire un schéma JSON riche avec tous les champs d'une offre d'emploi
2. WHEN des informations manquent THEN le système SHALL utiliser null plutôt que des valeurs inventées
3. WHEN des salaires sont mentionnés THEN ils SHALL être normalisés en XOF avec min/max/currency/period
4. IF des dates sont présentes THEN elles SHALL être formatées en YYYY-MM-DD
5. WHEN l'extraction est terminée THEN le JSON SHALL être validé contre un schéma défini

### Requirement 5: Orchestration Stage 2 dans le Workflow Existant

**User Story:** En tant qu'orchestrateur, je veux pouvoir exécuter l'Étape 2 enrichie en complément de l'Étape 1 existante, afin d'offrir des données plus riches sans casser le workflow actuel.

#### Acceptance Criteria

1. WHEN l'orchestrateur exécute un cycle complet THEN il SHALL pouvoir choisir entre Stage 1 seul ou Stage 1 + Stage 2
2. WHEN Stage 2 est activé THEN il SHALL traiter les URLs découvertes par Stage 1
3. WHEN Stage 2 échoue pour une URL THEN l'orchestrateur SHALL continuer avec les autres URLs
4. IF Stage 2 est désactivé THEN le système SHALL fonctionner exactement comme avant
5. WHEN Stage 2 est terminé THEN les données SHALL être stockées avec processing_stage='stage2'

### Requirement 6: Correction des Nettoyeurs URL Défaillants

**User Story:** En tant que système de nettoyage d'URLs, je veux corriger les patterns regex défaillants identifiés dans le rapport de validation, afin de récupérer les données des sources EmploiTogo.info et YOP L-FRII.

#### Acceptance Criteria

1. WHEN EmploiTogo.info cleaner est corrigé THEN il SHALL utiliser le pattern r'^/emploitogo/[^/]+/?$'
2. WHEN YOP L-FRII cleaner est corrigé THEN il SHALL utiliser le pattern r'^/emploi/[^/]+/?$'
3. WHEN les corrections sont appliquées THEN les tests SHALL confirmer 100% de succès pour ces sources
4. IF les patterns sont modifiés THEN ils SHALL être testés avec des URLs réelles
5. WHEN les corrections sont validées THEN elles SHALL être déployées en priorité

### Requirement 7: Tests de Régression et Validation

**User Story:** En tant que système de qualité, je veux des tests complets qui valident que les nouvelles fonctionnalités n'impactent pas l'existant, afin de garantir la stabilité du système.

#### Acceptance Criteria

1. WHEN des modifications sont apportées THEN tous les tests existants SHALL continuer de passer
2. WHEN Stage 2 est testé THEN il SHALL avoir ses propres tests unitaires et d'intégration
3. WHEN les nettoyeurs sont corrigés THEN des tests de régression SHALL valider le fix
4. IF un test échoue THEN la cause SHALL être identifiée et corrigée avant déploiement
5. WHEN tous les tests passent THEN le système SHALL être considéré comme stable

### Requirement 8: Monitoring et Observabilité Stage 2

**User Story:** En tant qu'opérateur système, je veux surveiller les performances et la qualité de l'Étape 2, afin de détecter les problèmes et optimiser le système.

#### Acceptance Criteria

1. WHEN Stage 2 s'exécute THEN il SHALL logger les métriques de performance par étape
2. WHEN une extraction échoue THEN l'erreur SHALL être loggée avec le contexte complet
3. WHEN un cycle Stage 2 est terminé THEN un rapport de synthèse SHALL être généré
4. IF la qualité des données baisse THEN des alertes SHALL être envoyées
5. WHEN des métriques sont collectées THEN elles SHALL inclure temps d'exécution, taux de succès, et qualité des données

### Requirement 9: Configuration Progressive par Source

**User Story:** En tant qu'administrateur, je veux pouvoir activer Stage 2 progressivement par source, afin de valider le système étape par étape sans risquer l'ensemble.

#### Acceptance Criteria

1. WHEN une source est configurée pour Stage 2 THEN elle SHALL pouvoir être activée/désactivée indépendamment
2. WHEN Stage 2 est activé pour une source THEN les autres sources SHALL continuer en Stage 1
3. WHEN une source Stage 2 échoue THEN elle SHALL automatiquement fallback vers Stage 1
4. IF tous les tests passent pour une source THEN Stage 2 SHALL pouvoir être activé pour la source suivante
5. WHEN toutes les sources sont validées THEN Stage 2 SHALL pouvoir être activé globalement

### Requirement 10: Préparation Phase 2.2 (Fonctionnalités Avancées)

**User Story:** En tant qu'architecte système, je veux préparer l'infrastructure pour les fonctionnalités avancées futures (Segmenter, Embeddings), afin de faciliter l'évolution vers Phase 2.2.

#### Acceptance Criteria

1. WHEN l'architecture est conçue THEN elle SHALL être extensible pour Jina Segmenter et Embeddings
2. WHEN la base de données est étendue THEN elle SHALL prévoir des colonnes pour content_chunks et description_embedding
3. WHEN les modèles sont définis THEN ils SHALL supporter les futures fonctionnalités
4. IF Phase 2.2 est implémentée THEN elle SHALL s'intégrer naturellement dans l'architecture existante
5. WHEN Phase 2.1 est stable THEN Phase 2.2 SHALL pouvoir être développée sans refactoring majeur

---

## Non-Functional Requirements

### Performance
- Stage 2 SHALL traiter au moins 10 jobs/minute
- L'ajout de Stage 2 SHALL avoir un impact < 10% sur les performances de Stage 1
- Les requêtes de base de données SHALL maintenir leurs temps de réponse actuels

### Reliability
- Stage 2 SHALL avoir un taux de disponibilité > 95%
- Les échecs de Stage 2 SHALL NOT impacter Stage 1
- Le système SHALL supporter un rollback complet en < 1 heure

### Scalability
- L'architecture SHALL supporter jusqu'à 50,000 jobs/jour en Stage 2
- Les colonnes ajoutées SHALL être optimisées pour les requêtes fréquentes
- Le système SHALL pouvoir traiter 6 sources simultanément

### Maintainability
- Le code Stage 2 SHALL suivre les mêmes standards que l'existant
- La configuration SHALL être documentée et validée
- Les logs SHALL être structurés et facilement analysables

---

## Success Criteria

### Phase 2.1 Success Metrics
- 100% des tests de régression passent
- 2 nettoyeurs URL corrigés avec 100% de succès
- Stage 2 produit des données pour au moins 3 sources
- Aucun impact négatif sur les performances de Stage 1
- Documentation complète et à jour

### Quality Metrics
- Taux de succès Stage 2 > 90%
- Qualité des données JSON > 85% (champs remplis)
- Temps de réponse moyen < 15 secondes/job
- Aucune régression détectée sur l'existant

---

*Requirements validés pour l'implémentation Phase 2.1 - Enhanced Data Pipeline*