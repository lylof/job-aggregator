"""
Script pour configurer la base de données PostgreSQL pour l'API Job Aggregator.
Ce script crée l'utilisateur et la base de données si nécessaire.
"""
import subprocess
import sys
import os
import time

def run_psql_command(command, as_postgres=True):
    """Exécuter une commande SQL via psql"""
    try:
        # Construire la commande avec les informations d'identification appropriées
        if as_postgres:
            # Utiliser l'utilisateur postgres (administrateur) pour créer l'utilisateur/base
            cmd = ['psql', '-U', 'postgres', '-c', command]
        else:
            # Utiliser l'utilisateur job_agg_user pour tester la connexion
            cmd = ['psql', '-U', 'job_agg_user', '-d', 'job_aggregator', '-c', command]
        
        # Exécuter la commande
        print(f"Exécution de: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Afficher le résultat
        if result.returncode == 0:
            print("Succès!")
            print(result.stdout)
            return True
        else:
            print("Erreur:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande: {e}")
        return False

def setup_database():
    """Configurer la base de données et l'utilisateur"""
    print("=== Configuration de la base de données PostgreSQL ===")
    
    # 1. Vérifier si PostgreSQL est accessible
    print("\n1. Vérification de l'accès à PostgreSQL...")
    if not run_psql_command("SELECT version();"):
        print("ERREUR: Impossible de se connecter à PostgreSQL avec l'utilisateur postgres.")
        print("Assurez-vous que PostgreSQL est installé et en cours d'exécution.")
        print("Vérifiez que l'utilisateur 'postgres' existe et que son mot de passe est correct.")
        return False
    
    # 2. Créer l'utilisateur job_agg_user s'il n'existe pas
    print("\n2. Création de l'utilisateur job_agg_user...")
    run_psql_command("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'job_agg_user') THEN
            CREATE USER job_agg_user WITH PASSWORD '1606';
        END IF;
    END
    $$;
    """)
    
    # 3. Créer la base de données si elle n'existe pas
    print("\n3. Création de la base de données job_aggregator...")
    run_psql_command("""
    SELECT 'CREATE DATABASE job_aggregator'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'job_aggregator')\\gexec
    """)
    
    # 4. Accorder les privilèges nécessaires
    print("\n4. Attribution des privilèges à l'utilisateur job_agg_user...")
    run_psql_command("GRANT ALL PRIVILEGES ON DATABASE job_aggregator TO job_agg_user;")
    
    # 5. Se connecter avec le nouvel utilisateur pour tester
    print("\n5. Test de connexion avec job_agg_user...")
    if run_psql_command("SELECT current_user, current_database();", as_postgres=False):
        print("\n=== Configuration terminée avec succès! ===")
        print("L'utilisateur job_agg_user et la base de données job_aggregator sont prêts.")
        return True
    else:
        print("\n=== Configuration terminée avec des avertissements ===")
        print("Impossible de tester la connexion avec job_agg_user.")
        return False

if __name__ == "__main__":
    setup_database()
