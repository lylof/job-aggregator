#!/usr/bin/env python3
"""
Script pour ajouter les nouveaux champs Phase 2 à la table items_cache dans Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis dans le .env")

def update_schema():
    """Met à jour le schéma de la table items_cache avec les nouveaux champs Phase 2"""
    
    print("🔧 MISE À JOUR DU SCHÉMA SUPABASE")
    print("=" * 50)
    print()
    print("⚠️  IMPORTANT : Vous devez ajouter ces colonnes manuellement dans Supabase !")
    print()
    print("📋 SQL À EXÉCUTER DANS L'ÉDITEUR SQL SUPABASE :")
    print("=" * 50)
    
    sql_commands = [
        "-- Classification automatique",
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS offer_category TEXT;",
        "",
        "-- Géolocalisation intelligente", 
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_city TEXT;",
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_region TEXT;",
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_latitude REAL;",
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_longitude REAL;",
        "",
        "-- Détection télétravail",
        "ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS remote_work_detected BOOLEAN DEFAULT FALSE;"
    ]
    
    for cmd in sql_commands:
        print(cmd)
    
    print("\n" + "=" * 50)
    print("📝 INSTRUCTIONS :")
    print("1. Connectez-vous à votre dashboard Supabase")
    print("2. Allez dans 'SQL Editor'")
    print("3. Copiez-collez le SQL ci-dessus")
    print("4. Cliquez sur 'Run'")
    print("5. Relancez le crawler : python quick_start.py")
    
    print("\n✅ Nouveaux champs Phase 2 à ajouter :")
    print("   - offer_category (TEXT) : Classification automatique")
    print("   - detected_city (TEXT) : Ville détectée")
    print("   - detected_region (TEXT) : Région détectée") 
    print("   - detected_latitude (REAL) : Latitude")
    print("   - detected_longitude (REAL) : Longitude")
    print("   - remote_work_detected (BOOLEAN) : Télétravail détecté")
    
    return True

if __name__ == "__main__":
    update_schema() 