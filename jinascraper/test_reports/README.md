# Rapports de Tests - JinaScraper

Ce dossier contient tous les rapports de tests du système JinaScraper.

## Structure des Rapports

- `YYYY-MM-DD_HH-MM_test-name.md` : Format des fichiers de rapport
- `latest_results.json` : Derniers résultats en format JSON
- `test_history.md` : Historique complet des tests

## Types de Tests

1. **Étape 1 - Exploration** : Test d'extraction d'URLs depuis les pages de listing
2. **Étape 2 - Analyse** : Test d'extraction et structuration du contenu des offres
3. **Services Individuels** : Test de chaque service (Jina, Gemini, Cache, Database)
4. **Orchestrateur** : Test du workflow complet
5. **Sources Spécifiques** : Test détaillé d'une source particulière

## Métriques Suivies

- **URLs extraites** par source
- **Temps de traitement** par étape
- **Taux de succès** par service
- **Qualité des données** extraites
- **Erreurs** rencontrées
- **Performance** générale

## Utilisation

Les rapports sont générés automatiquement par les scripts de test et sauvegardés ici pour référence future.