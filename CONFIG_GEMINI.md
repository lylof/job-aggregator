# CONFIGURATION GEMINI API
# ========================

# 1. Obtenez votre clé API Gemini :
#    https://makersuite.google.com/app/apikey

# 2. Configurez la variable d'environnement :
#    PowerShell: $env:GEMINI_API_KEY = "votre_cle_api_ici"
#    Bash: export GEMINI_API_KEY="votre_cle_api_ici"

# 3. Testez la configuration :
#    python -c "import os; print('Clé configurée:', bool(os.getenv('GEMINI_API_KEY')))"

# 4. Lancez le crawler avec enrichissement :
#    python crawler/run_crawl.py

# EXAMPLE DE CONFIGURATION POWERSHELL :
# $env:GEMINI_API_KEY = "AIzaSyD..."
# $env:PYTHONPATH = "."
# python crawler/run_crawl.py
