import requests
import time

class InPAScraper:
    BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
    PAGE_SIZE = 50

    def scrape_bandi_list(self, max_pages=10):
        page = 0
        bandi = []
        while True:
            url = f"{self.BASE_URL}?page={page}&size={self.PAGE_SIZE}"
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                content = data.get("content", [])
                if not content or (max_pages and page >= max_pages - 1):
                    break
                bandi.extend(content)
                print(f"Pagina {page}: {len(content)} bandi trovati")
                page += 1
                time.sleep(1)
            except Exception as e:
                print(f"Errore fetching pagina {page}: {e}")
                break

        print(f"Totale bandi trovati: {len(bandi)}")
        return bandi
