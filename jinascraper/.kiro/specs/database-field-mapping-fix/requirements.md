# Requirements Document

## Introduction

Le système JinaScraper fonctionne parfaitement pour l'extraction et le traitement des données, mais il y a un problème critique de sauvegarde en base de données. L'erreur `"Could not find the 'profile' column of 'jobs' in the schema cache"` indique un problème de mapping entre les champs générés par l'IA et le schéma de la base de données Supabase.

## Requirements

### Requirement 1

**User Story:** En tant que développeur système, je veux que les données extraites par l'IA soient correctement mappées vers les colonnes de la base de données, afin que tous les jobs traités soient sauvegardés avec succès.

#### Acceptance Criteria

1. WHEN l'IA génère un champ `profile` THEN le système SHALL le mapper vers `profile_description` dans la base
2. WHEN des champs IA ne correspondent pas exactement au schéma THEN le système SHALL appliquer un mapping automatique
3. WHEN une sauvegarde échoue pour un problème de champ THEN le système SHALL logger l'erreur avec détails du mapping

### Requirement 2

**User Story:** En tant qu'administrateur système, je veux que le système valide la compatibilité des données avant la sauvegarde, afin d'éviter les erreurs de schéma en production.

#### Acceptance Criteria

1. WHEN des données sont préparées pour la sauvegarde THEN le système SHALL valider tous les noms de champs
2. WHEN un champ invalide est détecté THEN le système SHALL le corriger automatiquement ou le supprimer
3. WHEN la validation échoue THEN le système SHALL continuer avec les champs valides et logger les problèmes

### Requirement 3

**User Story:** En tant que développeur, je veux un système de mapping flexible et configurable, afin de pouvoir facilement adapter les champs IA aux évolutions du schéma de base.

#### Acceptance Criteria

1. WHEN le schéma de base évolue THEN le mapping SHALL être facilement configurable
2. WHEN de nouveaux champs IA apparaissent THEN le système SHALL les gérer gracieusement
3. WHEN un mapping est appliqué THEN le système SHALL logger la transformation pour audit

### Requirement 4

**User Story:** En tant qu'utilisateur final, je veux que tous les jobs traités soient sauvegardés en base, afin de ne perdre aucune donnée extraite avec succès.

#### Acceptance Criteria

1. WHEN 25 jobs sont traités avec succès THEN 25 jobs SHALL être sauvegardés en base
2. WHEN une erreur de mapping survient THEN le job SHALL être sauvegardé avec les champs valides
3. WHEN la sauvegarde est complète THEN les statistiques SHALL refléter le nombre réel de jobs sauvegardés