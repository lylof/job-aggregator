from crawler.core.source_abc import AbstractSource
from crawler.extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema

class EmploitogoInfoSource(AbstractSource):
    @property
    def name(self):
        return "emploitogo_info"

    def get_listing_urls(self):
        return ["https://www.emploitogo.info/"]

    def get_listing_schema(self):
        """Schéma de la page de résultats (listing) pour emploitogo.info"""
        return {
            "name": "JobOffersEmploitogoInfo",
            "baseSelector": "article.hentry",
            "baseFields": [
                {"name": "url", "selector": "a.entry-image-link, h2.entry-title a", "type": "attribute", "attribute": "href"}
            ],
            "fields": [
                {"name": "title", "selector": "h2.entry-title a", "type": "text"},
                {"name": "date_posted", "selector": ".entry-meta .meta-date", "type": "text"},
                {"name": "excerpt", "selector": ".entry-excerpt", "type": "text"}
            ]
        }

    def get_detail_schema(self):
        """Schéma OPTIMISÉ pour les pages de détail emploitogo.info - RÉCUPÈRE TOUTES LES DONNÉES"""
        return {
            "name": "JobDetailEmploitogoInfo",
            "baseSelector": "body",
            "fields": [
                # === INFORMATIONS PRINCIPALES ===
                {"name": "title", "selector": "h1.entry-title, h1.page-title, h1", "type": "text"},
                {"name": "date_posted", "selector": ".entry-meta .meta-date, .post-date, .entry-date", "type": "text"},
                
                # === DESCRIPTION COMPLÈTE ===
                {"name": "job_description", "selector": "div.entry-content.article-content, .entry-content, .post-content, .content", "type": "html"},
                
                # === MÉTADONNÉES D'ARTICLE ===
                {"name": "author", "selector": ".entry-meta .meta-author, .author-name", "type": "text"},
                {"name": "categories", "selector": ".entry-categories a, .post-categories a", "type": "text"},
                {"name": "tags", "selector": ".entry-tags a, .post-tags a", "type": "text"},
                
                # === IMAGES ET MÉDIAS ===
                {"name": "featured_image", "selector": ".entry-featured img, .post-thumbnail img, .featured-image img", "type": "attribute", "attribute": "src"},
                {"name": "company_logo_url", "selector": ".company-logo img, .logo img", "type": "attribute", "attribute": "src"},
                
                # === EXTRACTION INTELLIGENTE DU CONTENU ===
                # Ces champs seront remplis par extraction intelligente du texte
                {"name": "company_name", "selector": ".company-name, .employer", "type": "text"},
                {"name": "location", "selector": ".location, .address", "type": "text"},
                {"name": "salary", "selector": ".salary, .remuneration", "type": "text"},
                {"name": "contract_type", "selector": ".contract-type, .job-type", "type": "text"},
                {"name": "contact_email", "selector": ".contact-email, .email", "type": "text"},
                {"name": "application_deadline", "selector": ".deadline, .expiry", "type": "text"},
                
                # === COMPÉTENCES ET QUALIFICATIONS ===
                {"name": "skills", "selector": ".skills, .competences, .requirements ul", "type": "html"},
                {"name": "experience_level", "selector": ".experience, .experience-required", "type": "text"},
                {"name": "education_level", "selector": ".education, .qualification", "type": "text"},
                
                # === INFORMATIONS SUPPLÉMENTAIRES ===
                {"name": "sector", "selector": ".sector, .industry", "type": "text"},
                {"name": "languages", "selector": ".languages, .langues", "type": "text"},
                {"name": "other_benefits", "selector": ".benefits, .avantages", "type": "html"},
                
                # === LIENS ET CONTACTS ===
                {"name": "application_url", "selector": ".apply-link a, .application-link a", "type": "attribute", "attribute": "href"},
                {"name": "company_website", "selector": ".company-website a, .website a", "type": "attribute", "attribute": "href"},
                {"name": "contact_phone", "selector": ".phone, .telephone", "type": "text"},
                
                # === DONNÉES BRUTES POUR EXTRACTION INTELLIGENTE ===
                {"name": "full_content", "selector": ".entry-content", "type": "text"},
                {"name": "raw_html", "selector": ".article-content", "type": "html"},
                
                # === MÉTADONNÉES WORDPRESS ===
                {"name": "post_id", "selector": "article", "type": "attribute", "attribute": "id"},
                {"name": "post_classes", "selector": "article", "type": "attribute", "attribute": "class"},
                
                # === COMMENTAIRES ET ENGAGEMENT ===
                {"name": "comments_count", "selector": ".comments-count, .comment-count", "type": "text"},
                {"name": "social_shares", "selector": ".social-share-count", "type": "text"}
            ]
        }

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
        
        # Format: "24 juin 2025"
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

    def extract_company_from_content(self, content):
        """Extrait intelligemment le nom de l'entreprise du contenu"""
        if not content:
            return None
            
        import re
        
        # Patterns pour identifier les entreprises
        patterns = [
            r"([A-Z][A-Za-z\s&-]+(?:SARL|SA|SAS|EURL|GIE|ONG|Association))",
            r"(L'entreprise\s+([A-Z][A-Za-z\s&-]+))",
            r"(La société\s+([A-Z][A-Za-z\s&-]+))",
            r"([A-Z][A-Za-z\s&-]+\s+recrute)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def extract_location_from_content(self, content):
        """Extrait intelligemment la localisation du contenu"""
        if not content:
            return None
            
        import re
        
        # Villes du Togo
        villes_togo = ['Lomé', 'Kpalimé', 'Atakpamé', 'Sokodé', 'Kara', 'Dapaong', 'Tsévié', 'Aného', 'Bassar', 'Niamtougou']
        
        for ville in villes_togo:
            if ville.lower() in content.lower():
                return ville
        
        # Patterns génériques de localisation
        patterns = [
            r"(Lomé|Kpalimé|Atakpamé|Sokodé|Kara|Dapaong|Tsévié|Aného|Bassar|Niamtougou)",
            r"à\s+([A-Z][a-z]+)",
            r"basé[e]?\s+à\s+([A-Z][a-z]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def extract_salary_from_content(self, content):
        """Extrait intelligemment le salaire du contenu"""
        if not content:
            return None
            
        import re
        
        # Patterns pour identifier les salaires
        patterns = [
            r"(\d+(?:\.\d+)?\s*(?:000)?\s*FCFA)",
            r"salaire\s*:?\s*([^\n]+)",
            r"rémunération\s*:?\s*([^\n]+)",
            r"(\d+\s*à\s*\d+\s*FCFA)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def get_item_unique_id(self, item_data):
        return item_data.get("url")

    def get_next_page_url(self, page_html, current_url):
        # Extraction de l'URL de la page suivante à partir du HTML (pagination)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_html, "html.parser")
        next_link = soup.select_one("a.pagi-item.pagi-icon.pagi-item-next")
        if next_link and next_link.has_attr("href"):
            return next_link["href"]
        return None
