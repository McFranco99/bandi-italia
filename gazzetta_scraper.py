import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

class GazzettaScraper:
    def __init__(self):
        self.base_url = "https://www.gazzettaufficiale.it"
        # URL pagina concorsi visibile e pubblica
        self.concorsi_url = f"{self.base_url}/ricercaArchivio/risultati?tipologia=CONC&testo=&dateRange=30"

    def scrape_ultimi_30_giorni(self):
        print("🔍 Inizio scraping Gazzetta Ufficiale - ultimi 30 giorni")
        bandi = []

        try:
            response = requests.get(self.concorsi_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Trova i container dei bandi — aggiornalo in base al DOM
            concorsi = soup.find_all("div", class_="card-atto__wrapper")

            print(f"📄 Trovati {len(concorsi)} bandi nella pagina")

            for concorso in concorsi:
                try:
                    # Titolo
                    title_el = concorso.find("h3", class_="card-atto__titolo")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)

                    # Link (completo)
                    link_el = concorso.find("a", href=True)
                    if link_el:
                        link = self.base_url + link_el['href']
                    else:
                        link = None

                    # Ente o categoria
                    ente_el = concorso.find("p", class_="card-atto__sottotitolo")
                    ente = ente_el.get_text(strip=True) if ente_el else "Ente pubblico"

                    # Descrizione (breve)
                    desc_el = concorso.find("p", class_="card-atto__descrizione")
                    descrizione = desc_el.get_text(strip=True) if desc_el else ""

                    # Data pubblicazione (tentativo parse)
                    data_pub = datetime.now().strftime('%Y-%m-%d')

                    bando = {
                        "id": abs(hash(link)) if link else int(time.time()),
                        "title": title,
                        "category": "lavoro",
                        "region": "nazionale",
                        "entity": ente,
                        "description": descrizione[:300],
                        "amount": 0,
                        "deadline": None,
                        "published": data_pub,
                        "url": link,
                        "source": "gazzetta_ufficiale"
                    }
                    bandi.append(bando)
                except Exception as e:
                    print(f"⚠️ Errore parsing bando: {e}")
        except Exception as e:
            print(f"❌ Errore scraping Gazzetta: {e}")

        print(f"✅ Totale bandi trovati da Gazzetta: {len(bandi)}")
        return bandi


if __name__ == "__main__":
    scraper = GazzettaScraper()
    risultati = scraper.scrape_ultimi_30_giorni()
    print(f"\nRisultati: {len(risultati)}")
