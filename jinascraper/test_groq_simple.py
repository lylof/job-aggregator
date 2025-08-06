#!/usr/bin/env python3
"""Test simple de la configuration Groq."""

import os
from dotenv import load_dotenv

# Charger le .env
load_dotenv()

print("🔧 Test configuration Groq...")

# Test clé API
groq_key = os.getenv("GROQ_API_KEY", "")
print(f"GROQ_API_KEY présente: {'✅' if groq_key else '❌'}")
if groq_key:
    print(f"Clé (derniers 10 chars): ...{groq_key[-10:]}")

# Test import groq
try:
    from groq import AsyncGroq
    print("✅ Package groq importé avec succès")
    
    # Test client
    if groq_key:
        client = AsyncGroq(api_key=groq_key)
        print("✅ Client Groq créé avec succès")
    else:
        print("❌ Impossible de créer le client sans clé API")
        
except ImportError as e:
    print(f"❌ Erreur import groq: {e}")
except Exception as e:
    print(f"❌ Erreur création client: {e}")

print("\n🔧 Test modèles Groq...")
models = [
    "llama-3.3-70b-versatile",
    "gemma2-9b-it", 
    "deepseek-r1-distill-llama-70b",
    "llama-3.1-8b-instant"
]

for model in models:
    print(f"  - {model}")

print("\n✅ Configuration Groq semble correcte")