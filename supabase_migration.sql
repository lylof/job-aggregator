-- Migration pour ajouter les nouveaux champs Phase 2 à la table items_cache
-- À exécuter dans l'éditeur SQL de Supabase

-- Classification automatique
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS offer_category TEXT;

-- Géolocalisation intelligente
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_city TEXT;
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_region TEXT;
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_latitude REAL;
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS detected_longitude REAL;

-- Détection télétravail
ALTER TABLE items_cache ADD COLUMN IF NOT EXISTS remote_work_detected BOOLEAN DEFAULT FALSE; 