#!/usr/bin/env python3
"""Test d'initialisation du service Groq."""

import os
import sys
sys.path.insert(0, '.')

def test_groq_initialization():
    """Test l'initialisation du service Groq."""
    print("🔧 Test initialisation GroqService...")
    
    try:
        # Test import avec le bon chemin
        import importlib.util
        spec = importlib.util.spec_from_file_location("groq_service", "services/groq_service.py")
        groq_module = importlib.util.module_from_spec(spec)
        
        # Simuler les imports nécessaires
        import sys
        from unittest.mock import MagicMock
        
        # Mock des dépendances
        sys.modules['jinascraper.config'] = MagicMock()
        sys.modules['jinascraper.models'] = MagicMock()
        
        # Maintenant essayer l'import
        spec.loader.exec_module(groq_module)
        GroqService = groq_module.GroqService
        print("✅ Import GroqService réussi")
        
        # Test initialisation
        groq = GroqService()
        print("✅ GroqService initialisé avec succès")
        print(f"Modèles configurés: {groq.models}")
        print(f"Clés configurées: {len(groq.api_keys)}")
        print(f"Modèle sélectionné: {groq._select_best_model()}")
        
        # Test clé API
        current_key = groq._current_key()
        if current_key:
            print(f"✅ Clé API disponible: {current_key[-10:]}")
        else:
            print("❌ Aucune clé API disponible")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur initialisation GroqService: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_groq_initialization()
    sys.exit(0 if success else 1)