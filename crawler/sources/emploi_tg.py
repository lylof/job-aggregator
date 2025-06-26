from crawler.core.source_abc import AbstractSource
from crawler.extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema

class EmploiTgSource(AbstractSource):
    @property
    def name(self):
        return "emploi_tg"

    def get_listing_urls(self):
        return ["https://www.emploi.tg/recherche-jobs-togo"]

    def get_listing_schema(self):
        """Schéma de la page de résultats (listing) pour emploi.tg avec nouveaux sélecteurs."""
        return {
            "name": "JobOffersTG",
            "baseSelector": "div.card.card-job",  # CORRIGÉ: Nouveau sélecteur trouvé
            "baseFields": [
                {"name": "url", "selector": "a[href*='/offre-emploi-togo/']", "type": "attribute", "attribute": "href"}
            ],
            "fields": [
                {"name": "title", "selector": "a[href*='/offre-emploi-togo/']", "type": "text"},
                {"name": "location", "selector": ".job-location, .location", "type": "text"},
                {"name": "company_name", "selector": ".company-name, .employer", "type": "text"},
                {"name": "date_posted", "selector": ".date-posted, .job-date", "type": "text"}
            ]
        }

    def get_detail_schema(self):
        """Schéma OPTIMISÉ pour les pages de détail emploi.tg - RÉCUPÈRE TOUTES LES DONNÉES"""
        return {
            "name": "JobDetailTG",
            "baseSelector": "body",
            "fields": [
                # === INFORMATIONS PRINCIPALES ===
                {"name": "title", "selector": "h1.text-center, h1.job-title, h1", "type": "text"},
                {"name": "company_name", "selector": ".company-name, .employer-name, .card-block-company h3, .job-info .company", "type": "text"},
                {"name": "location", "selector": ".job-location, .location, .address", "type": "text"},
                {"name": "date_posted", "selector": ".date-posted, .job-date, .publication-date", "type": "text"},
                
                # === DESCRIPTION COMPLÈTE ===
                {"name": "job_description", "selector": "div.job-description, .job-content, .description-content", "type": "html"},
                
                # === DÉTAILS DU POSTE ===
                {"name": "contract_type", "selector": ".contract-type, .job-type, .employment-type", "type": "text"},
                {"name": "salary", "selector": ".salary, .remuneration, .pay", "type": "text"},
                {"name": "experience_level", "selector": ".experience, .experience-required, .exp-level", "type": "text"},
                {"name": "education_level", "selector": ".education, .qualification, .diploma", "type": "text"},
                
                # === COMPÉTENCES ET QUALIFICATIONS ===
                {"name": "skills", "selector": ".skills, .competences, .job-qualifications ul, .requirements ul", "type": "html"},
                {"name": "job_qualifications", "selector": "div.job-qualifications, .qualifications, .requirements", "type": "html"},
                
                # === INFORMATIONS ENTREPRISE ===
                {"name": "company_description", "selector": ".company-description, .about-company, .employer-info", "type": "html"},
                {"name": "company_logo_url", "selector": ".company-logo img, .employer-logo img", "type": "attribute", "attribute": "src"},
                {"name": "company_website", "selector": ".company-website a, .employer-website a", "type": "attribute", "attribute": "href"},
                
                # === CONTACT ET APPLICATION ===
                {"name": "contact_email", "selector": ".contact-email, .email", "type": "text"},
                {"name": "application_url", "selector": ".apply-button a, .apply-link", "type": "attribute", "attribute": "href"},
                {"name": "contact_phone", "selector": ".phone, .telephone, .contact-phone", "type": "text"},
                
                # === MÉTADONNÉES ===
                {"name": "valid_through", "selector": ".deadline, .expiry-date, .valid-until", "type": "text"},
                {"name": "number_of_positions", "selector": ".positions, .postes, .vacancies", "type": "text"},
                {"name": "sector", "selector": ".sector, .industry, .domain", "type": "text"},
                {"name": "languages", "selector": ".languages, .langues", "type": "text"},
                
                # === AVANTAGES ===
                {"name": "other_benefits", "selector": ".benefits, .avantages, .perks", "type": "html"},
                
                # === DONNÉES BRUTES POUR ANALYSE ===
                {"name": "raw_job_info", "selector": ".job-info, .job-details, .job-meta", "type": "html"},
                {"name": "all_text_content", "selector": ".job-content, .main-content", "type": "text"}
            ]
        }

    def get_item_unique_id(self, item_data):
        return item_data.get("url")

    def get_next_page_url(self, page_html, current_url):
        # À compléter : logique pour trouver l'URL de la page suivante sur emploi.tg
        # Peut utiliser BeautifulSoup ou autre si besoin
        return None

    def normalize_date(self, date_str):
        """Normalise les dates du format français vers le format ISO"""
        if not date_str:
            return None
            
        # Mapping des mois français
        mois_fr = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        date_str = date_str.strip().lower()
        
        # Format: "25 juin 2025"
        for mois_fr_nom, mois_num in mois_fr.items():
            if mois_fr_nom in date_str:
                parts = date_str.split()
                if len(parts) >= 3:
                    try:
                        jour = parts[0].zfill(2)
                        annee = parts[2]
                        return f"{annee}-{mois_num}-{jour}"
                    except:
                        continue
        
        return date_str
