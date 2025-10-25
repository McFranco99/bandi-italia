"""
Scraper per Gazzetta Ufficiale Concorsi
Fonte: https://www.gazzettaufficiale.it/
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class GazzettaScraper:
    def __init__(self):
        self.base_url = "https://www.gazzettaufficiale.it"
        self.concorsi_url = f"{self.base_url}/gazzetta/concorsi"
        
    def scrape_ultimi_30_giorni(self):
        """Scrape concorsi pubblicati negli ultimi 30 giorni"""
        print("🔍 Inizio scraping Gazzetta Ufficiale (ultimi 30 giorni)...")
        
        bandi = []
        
        try:
            url = f"{self.base_url}/30giorni/concorsi"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trova tutti i link alle gazzette
            gazzette_links = soup.find_all('a', href=re.compile(r'/gazzetta/concorsi/caricaDettaglio'))
            
            print(f"📄 Trovate {len(gazzette_links)} gazzette da analizzare")
            
            # Limita a ultime 5 gazzette per performance
            for link in gazzette_links[:5]:
                href = link.get('href')
                if href:
                    full_url = f"{self.base_url}{href}"
                    bandi_gazzetta = self.scrape_gazzetta_dettaglio(full_url)
                    bandi.extend(bandi_gazzetta)
            
            print(f"✅ Gazzetta Ufficiale: {len(bandi)} bandi totali trovati")
            
        except Exception as e:
            print(f"❌ Errore scraping Gazzetta: {e}")
        
        return bandi
    
    def scrape_gazzetta_dettaglio(self, url):
        """Scrape dettaglio singola gazzetta"""
        bandi = []
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trova tutti i concorsi nella gazzetta
            concorsi = soup.find_all('div', class_='atto')
            
            for concorso in concorsi[:20]:  # Max 20 per gazzetta
                try:
                    title_elem = concorso.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    # Estrai ente
                    ente = "Ente Pubblico"
                    if concorso.find('strong'):
                        ente = concorso.find('strong').get_text(strip=True)
                    
                    # Descrizione
                    descrizione = concorso.get_text(strip=True)[:300]
                    
                    bando = {
                        'id': abs(hash(link)),
                        'title': title,
                        'category': 'lavoro',
                        'region': 'nazionale',
                        'entity': ente,
                        'description': descrizione,
                        'amount': 0,
                        'deadline': None,
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'url': f"{self.base_url}{link}" if link.startswith('/') else link,
                        'source': 'gazzetta_ufficiale'
                    }
                    
                    bandi.append(bando)
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"⚠️ Errore dettaglio gazzetta: {e}")
        
        return bandi

if __name__ == '__main__':
    scraper = GazzettaScraper()
    bandi = scraper.scrape_ultimi_30_giorni()
    print(f"\n✅ Totale bandi Gazzetta: {len(bandi)}")
