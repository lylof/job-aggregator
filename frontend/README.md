# Job Aggregator Frontend

Une interface utilisateur moderne pour le Job Aggregator, construite avec Next.js, TypeScript et Tailwind CSS.

## Structure du projet

```
/src
├── app/               # Pages et layouts avec App Router de Next.js
├── components/        # Composants UI réutilisables
│   ├── layout/        # Composants de structure (Header, Footer, etc.)
│   ├── jobs/          # Composants liés aux offres d'emploi
│   └── filters/       # Composants de filtrage et recherche
├── hooks/             # Hooks React personnalisés
├── services/          # Services d'API et utilitaires
├── types/             # Types TypeScript
└── utils/             # Fonctions utilitaires
```

## Fonctionnalités principales

- Affichage des offres d'emploi dans une interface inspirée de Dribbble Job Board
- Filtrage avancé par technologies, localisation, type de contrat, etc.
- Recherche textuelle
- Affichage détaillé des offres
- Design responsive et moderne

## Installation

```bash
# Installation des dépendances
npm install

# Démarrage du serveur de développement
npm run dev
```

## Connexion à l'API

L'application se connecte à l'API Job Aggregator qui expose les données des offres d'emploi enrichies.
