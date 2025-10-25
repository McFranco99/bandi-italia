"""
Scraper per MIMIT (Ministero Imprese e Made in Italy)
Fonte: https://www.mimit.gov.it/it/incentivi
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class MIMITScraper:
    def __init__(self):
        self.base_url = "https://www.mimit.gov.it"
        self.incentivi_url = f"{self.base_url}/it/incentivi"
        
    def scrape_incentivi(self):
        """Scrape incentivi e bandi MIMIT"""
        print("🔍 Inizio scraping MIMIT (Incentivi imprese)...")
        
        bandi = []
        
        try:
            response = requests.get(self.incentivi_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trova tutti i link agli incentivi
            incentivi_links = soup.find_all('a', href=re.compile(r'/it/incentivi/'))
            
            print(f"📋 Trovati {len(incentivi_links)} incentivi da analizzare")
            
            seen_urls = set()
            
            for link in incentivi_links[:30]:  # Limita a 30
                href = link.get('href')
                if not href or href in seen_urls:
                    continue
                
                seen_urls.add(href)
                
                full_url = f"{self.base_url}{href}" if href.startswith('/') else href
                
                # Estrai titolo
                title = link.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                bando = {
                    'id': abs(hash(full_url)),
                    'title': title,
                    'category': 'imprese',
                    'region': 'nazionale',
                    'entity': 'MIMIT - Ministero Imprese e Made in Italy',
                    'description': f"Incentivo per imprese: {title}",
                    'amount': 0,
                    'deadline': None,
                    'published': datetime.now().strftime('%Y-%m-%d'),
                    'url': full_url,
                    'source': 'mimit'
                }
                
                bandi.append(bando)
            
            print(f"✅ MIMIT: {len(bandi)} incentivi trovati")
            
        except Exception as e:
            print(f"❌ Errore scraping MIMIT: {e}")
        
        return bandi

if __name__ == '__main__':
    scraper = MIMITScraper()
    bandi = scraper.scrape_incentivi()
    print(f"\n✅ Totale bandi MIMIT: {len(bandi)}")
