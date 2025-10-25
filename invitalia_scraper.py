"""
Scraper per Invitalia
Fonte: https://www.invitalia.it
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime

class InvitaliaScraper:
    def __init__(self):
        self.base_url = "https://www.invitalia.it"
        
    def scrape_incentivi(self):
        """Scrape incentivi Invitalia"""
        print("🔍 Inizio scraping Invitalia...")
        
        bandi = []
        
        # URL principali Invitalia
        urls_da_scrapare = [
            f"{self.base_url}/cosa-facciamo/creiamo-nuove-aziende",
            f"{self.base_url}/cosa-facciamo/rafforziamo-le-imprese",
            f"{self.base_url}/incentivi-e-servizi"
        ]
        
        try:
            for url in urls_da_scrapare:
                try:
                    response = requests.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Cerca link agli incentivi
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href')
                        title = link.get_text(strip=True)
                        
                        # Filtra solo incentivi rilevanti
                        if not title or len(title) < 15:
                            continue
                        
                        if 'incentiv' in title.lower() or 'fondo' in title.lower() or 'impresa' in title.lower():
                            full_url = f"{self.base_url}{href}" if href.startswith('/') else href
                            
                            bando = {
                                'id': abs(hash(full_url)),
                                'title': title,
                                'category': 'investimenti',
                                'region': 'nazionale',
                                'entity': 'Invitalia',
                                'description': f"Incentivo Invitalia: {title}",
                                'amount': 0,
                                'deadline': None,
                                'published': datetime.now().strftime('%Y-%m-%d'),
                                'url': full_url,
                                'source': 'invitalia'
                            }
                            
                            bandi.append(bando)
                    
                except Exception as e:
                    print(f"⚠️ Errore URL {url}: {e}")
                    continue
            
            # Rimuovi duplicati
            bandi_unici = []
            urls_visti = set()
            for bando in bandi:
                if bando['url'] not in urls_visti:
                    urls_visti.add(bando['url'])
                    bandi_unici.append(bando)
            
            print(f"✅ Invitalia: {len(bandi_unici)} incentivi trovati")
            return bandi_unici[:20]  # Max 20
            
        except Exception as e:
            print(f"❌ Errore scraping Invitalia: {e}")
            return []

if __name__ == '__main__':
    scraper = InvitaliaScraper()
    bandi = scraper.scrape_incentivi()
    print(f"\n✅ Totale bandi Invitalia: {len(bandi)}")
