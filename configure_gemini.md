# 🚀 Configuration de l'Enrichissement LLM Automatique

## 📋 Étapes de Configuration

### 1. Obtenir une Clé API Gemini (GRATUITE)

1. **Aller sur [Google AI Studio](https://aistudio.google.com/)**
2. **Se connecter** avec un compte Google
3. **Cliquer sur "Get API Key"**
4. **Créer une nouvelle clé** (gratuite, 60 requêtes/minute)
5. **Copier la clé** (format: `AIza...`)

### 2. Configurer la Variable d'Environnement

#### Windows (PowerShell)
```powershell
# Temporaire (session actuelle)
$env:GEMINI_API_KEY = "VOTRE_CLE_ICI"

# Permanent (optionnel)
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "VOTRE_CLE_ICI", "User")
```

#### Linux/Mac
```bash
# Temporaire
export GEMINI_API_KEY="VOTRE_CLE_ICI"

# Permanent (ajoutez au .bashrc/.zshrc)
echo 'export GEMINI_API_KEY="VOTRE_CLE_ICI"' >> ~/.bashrc
```

### 3. Créer un fichier .env (Recommandé)

```bash
# Dans le dossier racine du projet
echo "GEMINI_API_KEY=VOTRE_CLE_ICI" > .env
```

### 4. Tester l'Enrichissement

```bash
cd crawler
python main_crawler.py
```

**Vérifications :**
- ✅ Pas de message `[WARN] GEMINI_API_KEY non défini`
- ✅ Messages `[LLM enrich] JSON parsing OK`
- ✅ Champs enrichis visibles dans l'API

## 🔧 Alternative : Enrichissement Local

Si vous préférez éviter les API externes, modifiez `crawler/main_crawler.py` :

```python
# Ligne 31, remplacez :
ENRICH_LLM = True  # Mettre à False pour désactiver l'enrichissement LLM

# Par :
ENRICH_LLM = False  # On utilise l'enrichissement local
ENABLE_LOCAL_ENRICHMENT = True  # Nouveau flag
```

Et ajoutez cette fonction d'enrichissement local :

```python
def local_enrichment(job_data):
    """Enrichissement basé sur des règles locales"""
    title = job_data.get('item_title', '').lower()
    description = job_data.get('item_description', '').lower()
    
    # Logique d'enrichissement par mots-clés
    if any(word in title + description for word in ['développeur', 'informatique']):
        return {
            'sector': 'Informatique & Technologie',
            'skills': ['Programming', 'Development'],
            'experience_level': 'Intermédiaire'
        }
    # ... autres règles
    
    return {}
```

## 📊 Résultats Attendus

Après configuration, vos offres d'emploi afficheront :
- 💰 **Salaires** au lieu de "À négocier"
- 🏢 **Secteurs** au lieu de "Non spécifié"  
- 🎯 **Compétences** visibles
- 📊 **Niveaux d'expérience** définis
- 🏠 **Télétravail** indiqué si applicable

## 🔍 Dépannage

### Problème : Enrichissement ne fonctionne pas
```bash
# Vérifier la variable
echo $env:GEMINI_API_KEY  # Windows
echo $GEMINI_API_KEY      # Linux/Mac

# Tester l'API directement
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=VOTRE_CLE" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'
```

### Problème : Quotas dépassés
- ✅ API Gemini gratuite : 60 req/min, 1500 req/jour
- ✅ Pour plus : upgrader vers Gemini Pro

### Problème : Données non mises à jour
```bash
# Forcer un nouveau crawl
cd crawler
rm last_scrap.json
python main_crawler.py
``` 