import requests
from bs4 import BeautifulSoup
from datetime import datetime

class GazzettaScraper:
    def __init__(self):
        self.base_url = "https://www.gazzettaufficiale.it"
        # Pagina che elenca i concorsi attivi ordinati per pubblicazione
        self.concorsi_url = f"{self.base_url}/concorsi/concorsi/elenco"

    def scrape_bandi_attivi(self, max_bandi=50):
        print("🔍 Inizio scraping Gazzetta Ufficiale - elenco concorsi attivi")
        bandi = []

        try:
            response = requests.get(self.concorsi_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.select('li.rigaBando')

            print(f"📄 Trovati {len(rows)} bandi nella pagina")
            for row in rows[:max_bandi]:
                try:
                    title_el = row.find('span', class_='titolo')
                    title = title_el.get_text(strip=True) if title_el else "Senza titolo"
                    
                    ente_el = row.find('span', class_='ente')  # o altro selettore ente pubblicatore
                    ente = ente_el.get_text(strip=True) if ente_el else "Ente pubblico"
                    
                    descrizione = row.get_text(strip=True)[:200]
                    
                    link_el = row.find('a', href=True)
                    if link_el:
                        link = self.base_url + link_el['href']
                    else:
                        link = self.concorsi_url

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
                        'url': link,
                        'source': 'gazzetta_ufficiale'
                    }
                    bandi.append(bando)
                except Exception as er:
                    print(f"⚠️ Errore parser row: {er}")
                    continue

        except Exception as e:
            print(f"❌ Errore scraping Gazzetta: {e}")

        print(f"✅ Totale bandi trovati da Gazzetta: {len(bandi)}")
        return bandi

if __name__ == "__main__":
    scraper = GazzettaScraper()
    risultati = scraper.scrape_bandi_attivi()
    print(f"\nRisultati: {len(risultati)}")
