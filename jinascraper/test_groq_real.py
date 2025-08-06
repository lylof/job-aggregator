#!/usr/bin/env python3
"""Test réel du service Groq avec du contenu d'emploi."""

import asyncio
import sys
import os

# Ajouter le chemin pour les imports
sys.path.insert(0, '.')

async def test_groq_real():
    """Test le service Groq avec du contenu réel."""
    
    # Contenu d'exemple d'une offre d'emploi
    test_content = """
    ### Développeur Web - Lomé

    **Entreprise**: TechCorp Togo
    **Localisation**: Lomé, Togo
    **Type de contrat**: CDI
    **Expérience**: 2-3 ans

    **Description du poste**:
    Nous recherchons un développeur web expérimenté pour rejoindre notre équipe dynamique.

    **Missions**:
    - Développement d'applications web
    - Maintenance des systèmes existants
    - Collaboration avec l'équipe technique

    **Profil recherché**:
    - Diplôme en informatique (Bac+3 minimum)
    - Maîtrise de PHP, JavaScript, MySQL
    - Expérience avec les frameworks modernes

    **Salaire**: 300,000 - 500,000 XOF/mois
    """
    
    try:
        # Import du service
        from services.groq_service import GroqService
        print("✅ Import GroqService réussi")
        
        # Initialisation
        groq = GroqService()
        print("✅ GroqService initialisé")
        print(f"Modèles: {groq.models}")
        print(f"Clés: {len(groq.api_keys)}")
        
        # Test d'extraction
        print("\n🔧 Test extraction avec Groq...")
        result = await groq.structure_job_data(
            test_content, 
            "https://test.com/job/123",
            "test_site"
        )
        
        if result:
            print("✅ Extraction Groq réussie !")
            print(f"Titre: {result.get('title', 'N/A')}")
            print(f"Entreprise: {result.get('company', 'N/A')}")
            print(f"Localisation: {result.get('location', 'N/A')}")
            print(f"Méthode: {result.get('extraction_method', 'N/A')}")
            return True
        else:
            print("❌ Extraction Groq échouée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test Groq: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_groq_real())
    print(f"\n{'✅ Test réussi' if success else '❌ Test échoué'}")