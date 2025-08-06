---
inclusion: always
---

# 🎯 RÈGLES ESSENTIELLES JINASCRAPER (7 règles maximum)

## 📜 RÈGLE 1 : DOCUMENTER LES CHANGEMENTS SIGNIFICATIFS

Documente dans la mémoire avec `@memory save_memory` ou outils spécialisés :
- Pourquoi le changement est nécessaire
- Quels fichiers sont affectés
- Impact attendu sur le système

## 📜 RÈGLE 2 : TESTER AVANT DE MODIFIER LES COMPOSANTS CRITIQUES

Toujours utiliser `python -m jinascraper.cli diagnose` avant de modifier :
- core/orchestrator.py
- services/detail_scraper.py
- config/sources/emploi_tg.py
- cli.py

## 📜 RÈGLE 3 : CONSULTER L'ÉTAT ACTUEL AVANT D'AGIR

Avant toute action importante :
1. Consulter la mémoire : `@memory get_memory`
2. Vérifier l'état des composants critiques
3. Identifier les priorités actuelles

## 📜 RÈGLE 4 : DEMANDER CONFIRMATION POUR LES ACTIONS À RISQUE

Pour les actions qui pourraient :
- Casser un composant fonctionnel
- Introduire des breaking changes
- Affecter plusieurs sources de données
→ Demander explicitement : "Cette action est-elle sûre ?"

## 📜 RÈGLE 5 : MAINTENIR LA COHÉRENCE ARCHITECTURALE

Toujours vérifier que les changements :
- Respectent l'architecture en couches existante
- Ne créent pas de dépendances circulaires
- Sont cohérents avec les patterns établis

## 📜 RÈGLE 6 : UTILISER LES OUTILS DISPONIBLES EFFICACEMENT

Exploiter tous les MCP disponibles :
- Memory pour contexte persistant
- Context7 pour documentation technique
- TestSprite pour tests automatisés
- Jina pour extraction de contenu
- Sequential-thinking pour problèmes complexes

## 📜 RÈGLE 7 : VALIDER AVANT DE TERMINER

Avant de finir une session :
1. Confirmer que toutes les actions importantes sont documentées
2. Vérifier que les tests passent
3. Mettre à jour l'état du projet si nécessaire

## ⚡ MÉCANISME DE FLEXIBILITÉ

### Exceptions urgentes
En cas d'urgence critique :
1. Noter : "Action urgente - documentation à suivre"
2. Agir rapidement pour résoudre le problème
3. Documenter dès que possible

### Évolution des règles
Pour modifier ces règles :
1. Proposer le changement avec justification
2. Valider que ça améliore l'efficacité
3. Mettre à jour ce fichier

---
**Ces 7 règles couvrent 80% des cas importants avec une complexité minimale**