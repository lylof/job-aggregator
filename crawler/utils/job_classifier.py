#!/usr/bin/env python3
"""
Classificateur intelligent pour distinguer les types d'offres
"""

import re
from typing import Dict, Any

class JobClassifier:
    """Classifie automatiquement les offres selon leur contenu"""
    
    # Mots-clés par catégorie avec scores de priorité
    CATEGORIES = {
        'scholarship': {
            'keywords': ['bourse', 'bourses', 'scholarship', 'fondation', 'étudiant', 'étudiants', 
                        'université', 'master', 'doctorat', 'licence', 'formation diplomante'],
            'priority': 10  # Priorité haute
        },
        'internship': {
            'keywords': ['stage', 'stagiaire', 'intern', 'apprenti', 'apprentissage', 'formation pratique'],
            'priority': 8
        },
        'training': {
            'keywords': ['formation', 'cours', 'atelier', 'certification', 'diplôme', 'apprentissage'],
            'priority': 6
        },
        'volunteer': {
            'keywords': ['volontaire', 'bénévole', 'volunteer', 'mission humanitaire', 'association'],
            'priority': 7
        },
        'job': {
            'keywords': ['emploi', 'poste', 'recrutement', 'candidat', 'travail', 'CDI', 'CDD', 
                        'salaire', 'rémunération', 'embauche', 'carrière'],
            'priority': 5  # Priorité par défaut
        }
    }
    
    # Patterns spéciaux pour améliorer la détection
    SPECIAL_PATTERNS = {
        'scholarship': [
            r'bourse.*\d{4}',  # "Bourse 2025"
            r'fondation.*recrute',  # "Fondation ... recrute"
            r'programme.*bourse',  # "Programme de bourses"
            r'étudiant.*international'
        ],
        'internship': [
            r'stage.*\d+.*mois',  # "Stage 6 mois"
            r'stagiaire.*domaine',
            r'fin.*études'
        ],
        'job': [
            r'\d+.*postes',  # "8 postes"
            r'salaire.*fcfa',  # "Salaire ... FCFA"
            r'selon.*profil',  # "Selon le profil"
            r'expérience.*requise'
        ]
    }
    
    def __init__(self):
        """Initialise le classificateur"""
        pass
    
    def classify_offer(self, title: str, description: str, company_name: str = "") -> str:
        """
        Classifie une offre selon son contenu
        
        Args:
            title: Titre de l'offre
            description: Description complète
            company_name: Nom de l'entreprise
            
        Returns:
            str: Catégorie détectée ('job', 'scholarship', 'internship', etc.)
        """
        # Nettoyer et normaliser le texte
        text = f"{title} {description} {company_name}".lower()
        text = self._normalize_text(text)
        
        # Scores par catégorie
        scores = {}
        
        # 1. Vérifier les patterns spéciaux (score élevé)
        for category, patterns in self.SPECIAL_PATTERNS.items():
            pattern_score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_score += 20  # Score élevé pour patterns spéciaux
            
            if pattern_score > 0:
                scores[category] = scores.get(category, 0) + pattern_score
        
        # 2. Compter les mots-clés avec pondération
        for category, config in self.CATEGORIES.items():
            keyword_score = 0
            priority = config['priority']
            
            for keyword in config['keywords']:
                # Compte exacte du mot-clé
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                keyword_score += count * priority
            
            scores[category] = scores.get(category, 0) + keyword_score
        
        # 3. Logique spéciale pour améliorer la précision
        scores = self._apply_special_logic(text, scores)
        
        # 4. Retourner la catégorie avec le score le plus élevé
        if not scores or max(scores.values()) == 0:
            return 'job'  # Par défaut
        
        best_category = max(scores, key=scores.get)
        
        # Log pour debug
        print(f"[CLASSIFIER] '{title[:50]}...' -> {best_category} (scores: {scores})")
        
        return best_category
    
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour améliorer la détection"""
        # Remplacer les accents et caractères spéciaux
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _apply_special_logic(self, text: str, scores: Dict[str, int]) -> Dict[str, int]:
        """Applique une logique spéciale pour améliorer la classification"""
        
        # Si "emploitogo.info" dans le texte, probablement pas une vraie entreprise
        if 'emploitogo.info' in text:
            # Réduire le score "job" si c'est juste le site web
            if 'job' in scores:
                scores['job'] = max(0, scores['job'] - 10)
        
        # Si mention d'un montant en FCFA, probablement un job
        if re.search(r'\d+.*fcfa', text):
            scores['job'] = scores.get('job', 0) + 15
        
        # Si mention de "fondation" et "bourse", très probablement scholarship
        if 'fondation' in text and 'bourse' in text:
            scores['scholarship'] = scores.get('scholarship', 0) + 25
        
        # Si mention de "stage" et durée en mois, probablement internship
        if re.search(r'stage.*\d+.*mois', text):
            scores['internship'] = scores.get('internship', 0) + 20
        
        return scores
    
    def get_category_stats(self, items: list) -> Dict[str, int]:
        """
        Analyse les statistiques de classification sur une liste d'items
        
        Args:
            items: Liste d'offres avec 'title' et 'description'
            
        Returns:
            Dict: Statistiques par catégorie
        """
        stats = {}
        
        for item in items:
            category = self.classify_offer(
                item.get('title', ''),
                item.get('description', ''),
                item.get('company_name', '')
            )
            stats[category] = stats.get(category, 0) + 1
        
        return stats 