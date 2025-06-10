# 📋 Plan de Refactorisation du Crawler avec Crawl4AI

## 1. **Audit & Nettoyage du Code Actuel**
- [x] Lister tous les fichiers/fonctions liés au crawling/scraping.
- [x] Identifier les parties non conformes à la doc officielle ([docs](https://docs.crawl4ai.com/)).
- [x] Supprimer ou isoler le code spaghetti, les duplications, les hacks temporaires.

> **Note :** Le dossier `crawler1/` a été identifié comme code legacy. Il sera archivé sous le nom `crawler_legacy/` pour référence temporaire, puis supprimé après migration éventuelle d'utilitaires utiles.

---

## 2. **Structuration du Projet**
- [ ] Créer un dossier `crawler/` ou `scraper/` dédié.
- [ ] Créer les fichiers suivants :
  - [ ] `main_crawler.py` (point d'entrée principal pour lancer le crawl)
  - [ ] `config.py` (pour les configurations spécifiques au crawler)
  - [ ] `database_handler.py` (pour l'insertion dans PostgreSQL)
  - [ ] `models.py` (pour les schémas de données du crawler si différents de l'API)
  - [ ] `custom_crawler.py` (si des logiques de crawling spécifiques sont nécessaires)

---

## 3. **Implémentation du Crawler selon Crawl4AI**

### 3.1. **Configuration du Crawler**
- [ ] Définir la configuration de Crawl4AI en utilisant la classe `CrawlerConfig`.
- [ ] Configurer les `user_agent`, `cache_enabled`, `proxy_enabled`, `headless`.
- [ ] Intégrer les paramètres de `max_pages`, `max_depth`, `max_requests_per_second`.

### 3.2. **Définition des stratégies de crawling**
- [ ] Utiliser `WebCrawler` pour les pages web standard.
- [ ] Utiliser `AsyncWebCrawler` si des tâches asynchrones sont nécessaires.
- [ ] Envisager `LLMExtractionStrategy` pour l'extraction sémantique avancée.
- [ ] Mettre en place des `selectors` (CSS, XPath) pour cibler les éléments.
- [ ] Utiliser `regex_patterns` pour l'extraction de données complexes.

### 3.3. **Gestion des pages**
- [ ] Implémenter la fonction `process_page` pour traiter chaque page visitée.
- [ ] Extraire les données pertinentes (titre, description, URL, entreprise, etc.).
- [ ] Gérer la pagination et les liens internes/externes.

### 3.4. **Gestion des erreurs et logs**
- [ ] Utiliser les mécanismes de gestion d'erreurs de Crawl4AI (`on_error`, `on_4xx`, `on_5xx`).
- [ ] Mettre en place un système de logging (`logging` de Python) pour suivre l'avancement.

---

## 4. **Intégration de la Base de Données (PostgreSQL)**
- [ ] Déplacer la logique de connexion et d'insertion PostgreSQL dans `database_handler.py`.
- [ ] Assurer la compatibilité des types de données Python avec PostgreSQL.
- [ ] Utiliser `asyncpg` pour les opérations asynchrones sur la base de données.
- [ ] Gérer les transactions pour l'insertion des données.
- [ ] Implémenter la gestion des doublons et des mises à jour (upsert).

---

## 5. **Tests & Validation**
- [ ] Créer des tests unitaires pour les fonctions d'extraction et d'insertion.
- [ ] Créer des tests d'intégration pour vérifier le cycle complet (crawl -> insertion).
- [ ] Valider les données insérées directement dans la base de données.
- [ ] Exécuter le crawler sur un petit ensemble de pages pour valider le fonctionnement.

---

## 6. **Optimisation & Déploiement**
- [ ] Optimiser les sélecteurs CSS/XPath pour améliorer les performances.
- [ ] Mettre en place le cache de Crawl4AI pour éviter les requêtes inutiles.
- [ ] Gérer la rotation des proxys si nécessaire.
- [ ] Envisager le déploiement en Docker si le volume de crawl est important.

---

## 7. **Maintenance & Évolution**
- [ ] Mettre à jour régulièrement Crawl4AI pour bénéficier des dernières améliorations.
- [ ] Surveiller les logs et les performances du crawler en production.
- [ ] Adapter le crawler aux changements de structure des sites web ciblés.

---

## **Ressources Clés**
- **Documentation Crawl4AI :** [https://docs.crawl4ai.com/](https://docs.crawl4ai.com/)
- **Dépôt GitHub Crawl4AI :** [https://github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)


Ce plan sera ton guide. Nous allons avancer étape par étape pour le mettre en œuvre. Es-tu prêt à commencer par l'audit et le nettoyage du code actuel ? 