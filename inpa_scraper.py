import requests

class InPAScraper:
    BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
    PAGE_SIZE = 4  # valo massimo visto da XHR

    def scrape_bandi_list(self, max_pages=10):
        bandi = []
        headers = {'Content-Type': 'application/json'}
        for page in range(max_pages):
            params = {"page": page, "size": self.PAGE_SIZE}
            payload = {}  # nessun filtro viene inviato di default
            try:
                r = requests.post(self.BASE_URL, params=params, json=payload, headers=headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                content = data.get("content", [])
                if not content:
                    break
                bandi.extend(content)
                print(f"Pagina {page}: {len(content)} bandi trovati")
            except Exception as e:
                print(f"Errore InPA pagina {page}: {e}; risposta: {getattr(r, 'text', '')}")
                break
        return bandi
