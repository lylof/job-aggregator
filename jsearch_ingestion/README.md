# JSearch Ingestion Module

Ce module permet d'interroger l'API JSearch (via RapidAPI) et de transformer les résultats pour ingestion dans la base PostgreSQL du Job Board.

## Utilisation

1. Définir la variable d'environnement `JSEARCH_API_KEY` avec ta clé RapidAPI.
2. Lancer le script principal :

```bash
python -m jsearch_ingestion.main
```

## À faire
- Mapper tous les champs utiles selon le schéma `items_cache` du PRD.
- Ajouter l'export vers PostgreSQL/Supabase.
- Ajouter la gestion des erreurs et le logging avancé. 