import requests
import time

class InPAScraper:
    BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
    PAGE_SIZE = 4  # Questo è il valore visto nelle richieste dal portale reale

    def scrape_bandi_list(self, max_pages=20):
        bandi = []
        for page in range(max_pages):
            url = f"{self.BASE_URL}?page={page}&size={self.PAGE_SIZE}"
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                content = data.get("content", [])
                if not content:
                    break
                bandi.extend(content)
                print(f"Pagina {page}: {len(content)} bandi trovati")
                time.sleep(0.5)  # buona pratica per scraping etico
            except Exception as e:
                print(f"Errore InPA pagina {page}: {e}; risposta: {getattr(response, 'text', '')}")
                break
        return bandi
