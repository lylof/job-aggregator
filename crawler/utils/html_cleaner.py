"""
Module de nettoyage HTML pour le crawler
"""

import re
from html import unescape
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

def clean_html_content(html_content):
    """
    Nettoie le contenu HTML selon les bonnes pratiques
    
    Args:
        html_content (str): Contenu HTML à nettoyer
        
    Returns:
        str: Texte propre sans balises HTML
    """
    if not html_content:
        return ""
    
    # Si BeautifulSoup n'est pas disponible, fallback simple
    if not BeautifulSoup:
        # Suppression basique des balises HTML
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    try:
        # Utiliser BeautifulSoup pour un nettoyage robuste
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Supprimer scripts, styles, et autres éléments indésirables
        for element in soup(['script', 'style', 'meta', 'link', 'head']):
            element.decompose()
        
        # Extraire le texte propre
        text = soup.get_text(separator=' ')
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    except Exception as e:
        print(f"[WARN] Erreur nettoyage HTML avec BeautifulSoup: {e}")
        # Fallback en cas d'erreur
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

def extract_plain_text(html_or_text):
    """
    Extrait le texte brut d'un contenu HTML ou texte
    
    Args:
        html_or_text (str): Contenu à nettoyer
        
    Returns:
        str: Texte propre
    """
    if not html_or_text:
        return ""
    
    # Si le contenu contient du HTML, le nettoyer
    if '<' in html_or_text and '>' in html_or_text:
        return clean_html_content(html_or_text)
    
    # Sinon, retourner tel quel (nettoyage minimal)
    return html_or_text.strip()

# Test du module
if __name__ == "__main__":
    # Test avec du HTML sale
    dirty_html = """
    <div class="entry-content article-content">
        <div class="code-block" style="margin: 8px 0;">
            <script>alert("test");</script>
        </div>
        <p>Voici le <strong>contenu principal</strong> de l'offre d'emploi.</p>
        <style>body { color: red; }</style>
    </div>
    """
    
    clean_text = clean_html_content(dirty_html)
    print("Texte nettoyé:")
    print(repr(clean_text))
    print()
    print("Texte final:")
    print(clean_text)
