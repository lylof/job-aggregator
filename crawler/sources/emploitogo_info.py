from ..core.source_abc import AbstractSource
from ..extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema
import requests
from bs4 import BeautifulSoup
import re

class EmploitogoInfoSource(AbstractSource):
    @property
    def name(self):
        return "emploitogo_info"

    @property
    def use_fallback_http(self):
        """Utilise HTTP fallback pour éviter les problèmes WordPress JavaScript"""
        return True

    def get_listing_urls(self):
        return ["https://www.emploitogo.info/emploitogo/"]

    def fallback_http_crawl(self, url, is_listing=True):
        """
        Méthode fallback utilisant requests + BeautifulSoup
        pour contourner les problèmes WordPress JavaScript
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if is_listing:
                    return self._extract_listing_fallback(soup, url)
                else:
                    return self._extract_detail_fallback(soup, url)
            else:
                print(f"❌ HTTP Fallback failed: {response.status_code} for {url}")
                return None
                
        except Exception as e:
            print(f"💥 HTTP Fallback error: {e} for {url}")
            return None
    
    def _extract_listing_fallback(self, soup, base_url):
        """Extraction fallback pour la page de listing"""
        items = []
        
        # Sélecteurs WordPress standards pour les articles/posts
        article_selectors = [
            '.post', 'article', '.job-listing', '.job-item',
            '.entry', '.listing-item', '.post-item'
        ]
        
        articles = []
        for selector in article_selectors:
            found = soup.select(selector)
            if found:
                articles = found
                break
        
        for article in articles:
            # Extraire l'URL
            link = article.find('a')
            if link and link.get('href'):
                url = link['href']
                
                # Normaliser l'URL
                if url.startswith('/'):
                    url = 'https://www.emploitogo.info' + url
                elif not url.startswith('http'):
                    url = 'https://www.emploitogo.info/' + url
                
                # Extraire le titre
                title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title', '.entry-title']
                title = None
                for sel in title_selectors:
                    title_elem = article.select_one(sel)
                    if title_elem:
                        title = title_elem.get_text().strip()
                        break
                
                if not title and link:
                    title = link.get_text().strip()
                
                # Extraire la date
                date_selectors = ['.date', '.post-date', '.entry-date', '.meta-date']
                date_posted = None
                for sel in date_selectors:
                    date_elem = article.select_one(sel)
                    if date_elem:
                        date_posted = date_elem.get_text().strip()
                        break
                
                # Extraire excerpt
                excerpt_selectors = ['.excerpt', '.post-excerpt', '.summary']
                excerpt = None
                for sel in excerpt_selectors:
                    exc_elem = article.select_one(sel)
                    if exc_elem:
                        excerpt = exc_elem.get_text().strip()
                        break
                
                if title and url:
                    items.append({
                        'url': url,
                        'title': title,
                        'date_posted': date_posted,
                        'excerpt': excerpt
                    })
        
        return items if items else None
    
    def _extract_detail_fallback(self, soup, url):
        """Extraction fallback pour les pages de détail"""
        data = {'url': url}
        
        # Titre
        title_selectors = ['h1.entry-title', 'h1.page-title', 'h1', '.title']
        for sel in title_selectors:
            title_elem = soup.select_one(sel)
            if title_elem:
                data['title'] = title_elem.get_text().strip()
                break
        
        # Contenu principal
        content_selectors = [
            '.entry-content', '.post-content', '.content', '#content',
            '.article-content', '.job-description'
        ]
        for sel in content_selectors:
            content_elem = soup.select_one(sel)
            if content_elem:
                data['job_description'] = str(content_elem)
                data['full_content'] = content_elem.get_text().strip()
                break
        
        # Date
        date_selectors = ['.entry-date', '.post-date', '.date', '.meta-date']
        for sel in date_selectors:
            date_elem = soup.select_one(sel)
            if date_elem:
                data['date_posted'] = date_elem.get_text().strip()
                break
        
        # Extraction intelligente depuis le contenu
        if 'full_content' in data:
            content = data['full_content']
            
            # Entreprise
            company = self.extract_company_from_content(content)
            if company:
                data['company_name'] = company
            
            # Localisation
            location = self.extract_location_from_content(content)
            if location:
                data['location'] = location
            
            # Salaire
            salary = self.extract_salary_from_content(content)
            if salary:
                data['salary'] = salary
        
        return data

    def get_listing_schema(self):
        """Schéma de la page de résultats (listing) pour emploitogo.info - CORRIGÉ"""
        return {
            "name": "JobOffersEmploitogoInfo",
            "baseSelector": ".post-item",
            "baseFields": [
                {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"}
            ],
            "fields": [
                {"name": "title", "selector": "h3 a, .post-title a", "type": "text"},
                {"name": "date_posted", "selector": ".post-date, .meta-date", "type": "text"},
                {"name": "excerpt", "selector": ".post-excerpt, .excerpt", "type": "text"},
                {"name": "category", "selector": ".post-category", "type": "text"}
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
