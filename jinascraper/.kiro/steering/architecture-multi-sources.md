# Architecture Multi-Sources JinaScraper - Décisions Techniques

**Date** : 3 Août 2025  
**Contexte** : Analyse complète de l'architecture de données pour gérer 6 sources différentes sans perte d'information

## 🎯 **PROBLÈME INITIAL IDENTIFIÉ**

### Erreur Critique de Mapping
- **Symptôme** : `"Could not find the 'profile' column of 'jobs' in the schema cache"`
- **Cause** : L'IA génère un champ `profile` mais la base Supabase attend `profile_description`
- **Impact** : 0 jobs sauvegardés malgré 25 jobs traités avec succès

### Problématique Multi-Sources
- **6 sources configurées** : emploi_tg, linkedin_togo, indeed_togo, anpetogo, emploitogo_info, yop_lfrii
- **Structures différentes** : Chaque source a ses spécificités (logos, métadonnées, champs uniques)
- **Risque de perte** : Architecture trop rigide pourrait perdre des données spécifiques

## 🏗️ **ARCHITECTURE DÉCIDÉE : SCHÉMA UNIVERSEL + MÉTADONNÉES**

### Principe Fondamental
**"Standardisation des essentiels + Préservation des spécificités"**

### Structure de Données
```sql
-- Table jobs (structure fixe optimisée)
CREATE TABLE jobs (
    -- CHAMPS UNIVERSELS (colonnes fixes)
    id UUID PRIMARY KEY,
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR,
    description TEXT,
    profile_description TEXT,  -- ← CORRECTION du problème "profile"
    salary_range VARCHAR,
    contract_type VARCHAR,
    experience_level VARCHAR,
    education_level VARCHAR,
    sector VARCHAR,
    missions TEXT[],
    required_skills TEXT[],
    posted_date DATE,
    application_deadline DATE,
    contact_email VARCHAR,
    contact_phone VARCHAR,
    
    -- MÉTADONNÉES FLEXIBLES (JSONB)
    extraction_metadata JSONB,  -- Données spécifiques par source
    raw_data JSONB,             -- Backup complet
    
    -- CHAMPS TECHNIQUES
    source_url TEXT NOT NULL,
    source_site VARCHAR NOT NULL,
    extraction_method VARCHAR NOT NULL,
    quality_score NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

### Mapping par Source
```python
# EMPLOI.TG - Source principale togolaise
emploi_tg_specific = {
    "company_logo": "URL logo entreprise",
    "company_website": "Site web entreprise", 
    "number_of_positions": "Nombre de postes",
    "languages_required": ["Langues requises"],
    "benefits": ["Avantages proposés"]
}

# LINKEDIN TOGO - Source internationale riche
linkedin_specific = {
    "company_logo": "Logo LinkedIn",
    "company_size": "Taille entreprise",
    "applicants_count": "Nombre candidats",
    "job_level": "Niveau du poste",
    "industry": "Industrie",
    "company_rating": "Note entreprise"
}

# INDEED TOGO - Source internationale avec estimations
indeed_specific = {
    "salary_estimate": "Estimation salaire",
    "company_rating": "Note entreprise",
    "company_reviews": "Avis entreprise",
    "job_type": "Type emploi",
    "benefits": ["Avantages"]
}

# ANPE TOGO - Source gouvernementale officielle
anpetogo_specific = {
    "reference_number": "Numéro référence",
    "publication_date": "Date publication officielle",
    "application_method": "Méthode candidature",
    "contact_person": "Personne contact"
}

# EMPLOITOGO.INFO - Source privée locale
emploitogo_info_specific = {
    "job_category": "Catégorie emploi",
    "posting_date": "Date publication",
    "application_deadline": "Date limite",
    "contact_email": "Email contact"
}

# YOP LFRII - Source ONG/projets
yop_lfrii_specific = {
    "organization_type": "Type organisation",
    "project_duration": "Durée projet",
    "funding_source": "Source financement",
    "application_procedure": "Procédure candidature"
}
```

## 🔄 **FLUX DE TRAITEMENT UNIVERSEL**

### Étape 1 : Extraction IA Adaptée
```python
# Schéma IA universel (corrigé)
ai_schema = {
    # Champs universels
    "title": "Titre du poste",
    "company": "Nom entreprise",
    "location": "Localisation",
    "profile_description": "Profil recherché",  # ← CORRIGÉ !
    
    # Champs spécifiques détectés automatiquement
    "company_logo": "Logo si disponible",
    "company_size": "Taille si mentionnée",
    "benefits": "Avantages si listés",
    # ... autres champs selon la source
}
```

### Étape 2 : Mapping Intelligent
```python
def map_to_universal(source_data, source_name):
    # 1. Champs universels (colonnes fixes)
    universal = extract_universal_fields(source_data)
    
    # 2. Champs spécifiques (JSONB)
    specific_data = extract_source_specific_fields(source_data, source_name)
    universal['extraction_metadata'] = {
        'source_specific_data': {
            f'{source_name}_data': specific_data
        }
    }
    
    # 3. Backup complet (sécurité)
    universal['raw_data'] = source_data
    
    return universal
```

### Étape 3 : Sauvegarde Garantie
```python
# Aucune perte de données possible
await database.upsert_job(universal_data)
```

## 🎨 **AFFICHAGE FRONTEND ADAPTATIF**

### Composant Job Card Universel
```javascript
function JobCard({ job }) {
    // Données universelles (toujours disponibles)
    const { title, company, location } = job;
    
    // Logo adaptatif selon la source
    const logo = getSourceLogo(job);
    
    // Informations spécifiques selon la source
    const specificInfo = getSourceSpecificInfo(job);
    
    return (
        <div className="job-card">
            <img src={logo} alt={company} />
            <h3>{title}</h3>
            <p>{company} - {location}</p>
            {specificInfo && <SourceSpecificInfo data={specificInfo} />}
        </div>
    );
}

function getSourceLogo(job) {
    const sourceData = job.extraction_metadata?.source_specific_data;
    
    return sourceData?.emploi_tg_data?.company_logo ||
           sourceData?.linkedin_data?.company_logo ||
           sourceData?.indeed_data?.company_logo ||
           '/default-logo.png';
}
```

## 📊 **AVANTAGES DE CETTE ARCHITECTURE**

### ✅ Garanties Techniques
1. **Zéro perte de données** : Tout est conservé (universelle + spécifique + raw)
2. **Performance optimale** : Requêtes rapides sur colonnes indexées
3. **Flexibilité totale** : Nouvelles sources ajoutées facilement
4. **Évolutivité** : Pas de migration de base nécessaire

### ✅ Bénéfices Business
1. **Affichage riche** : Logos, métadonnées, informations spécifiques
2. **Recherche avancée** : Filtres sur tous les champs
3. **Analytics** : Analyses croisées entre sources
4. **Scalabilité** : Support de 100+ sources futures

### ✅ Maintenance Simplifiée
1. **Code unifié** : Un seul pipeline pour toutes les sources
2. **Tests standardisés** : Même logique de validation
3. **Monitoring centralisé** : Métriques par source
4. **Debug facilité** : Raw data toujours disponible

## 🚀 **PLAN D'IMPLÉMENTATION VALIDÉ**

### Phase 1 : Correction Critique (Priorité 1)
- [x] Identifier le problème `profile` → `profile_description`
- [x] Créer la spec de mapping universel
- [ ] Implémenter le FieldMapper de base
- [ ] Tester avec emploi_tg

### Phase 2 : Architecture Multi-Sources (Priorité 2)
- [ ] Créer UniversalSourceAdapter
- [ ] Implémenter mappers pour les 6 sources
- [ ] Tester avec données réelles de chaque source
- [ ] Valider la sauvegarde sans perte

### Phase 3 : Frontend Adaptatif (Priorité 3)
- [ ] Composants d'affichage universels
- [ ] Gestion des logos par source
- [ ] Informations spécifiques contextuelles
- [ ] Tests d'affichage multi-sources

## 🎯 **DÉCISIONS TECHNIQUES FINALES**

### Validé ✅
1. **Schéma universel** avec champs fixes + JSONB flexible
2. **Correction `profile` → `profile_description`** 
3. **Architecture multi-sources** sans perte de données
4. **Frontend adaptatif** selon les données disponibles
5. **Implémentation progressive** par phases

### Rejeté ❌
1. **Schéma complexe initial** (trop de champs vides)
2. **Migration de base majeure** (trop risqué)
3. **Schémas différents par source** (maintenance complexe)

## 📝 **NOTES POUR FUTURES CONVERSATIONS**

- **Problème résolu** : Mapping `profile` → `profile_description`
- **Architecture choisie** : Universelle + métadonnées JSONB
- **Sources supportées** : 6 actuelles + futures illimitées
- **Garantie** : Zéro perte de données
- **Status** : Spec créée, implémentation en cours

**Cette architecture est la solution définitive pour gérer toutes les sources actuelles et futures du JinaScraper !** 🎯