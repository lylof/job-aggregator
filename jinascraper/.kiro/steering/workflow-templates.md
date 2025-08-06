---
inclusion: manual
---

# 🔄 TEMPLATES DE WORKFLOW (Optionnels)

## 🐛 TEMPLATE : CORRECTION DE BUG

1. Consulter mémoire : `@memory search_memory query="[problème]"`
2. Identifier les fichiers affectés
3. Tester avec CLI : `python -m jinascraper.cli diagnose`
4. Appliquer la correction
5. Tester à nouveau avec CLI
6. Documenter : `@memory save_bug_fix description="..."`

## ✨ TEMPLATE : AJOUT DE FONCTIONNALITÉ

1. Analyser l'impact sur l'architecture
2. Consulter les spécifications existantes
3. Implémenter la fonctionnalité
4. Tester avec CLI
5. Documenter : `@memory save_feature description="..."`

## ⚙️ TEMPLATE : CHANGEMENT DE CONFIGURATION

1. Sauvegarder la configuration actuelle
2. Appliquer les changements
3. Tester avec CLI
4. Documenter : `@memory save_config description="..."`

---
*Templates optionnels pour standardiser les workflows courants*