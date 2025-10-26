import requests

class InPAScraper:
    BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
    PAGE_SIZE = 4  # massimo accettato da InPA

    def scrape_bandi_list(self, max_pages=10):
        bandi = []
        headers = {'Content-Type': 'application/json'}
        for page in range(max_pages):
            params = {"page": page, "size": self.PAGE_SIZE}
            payload = {}
            try:
                r = requests.post(self.BASE_URL, params=params, json=payload, headers=headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                content = data.get("content", [])
                if not content:
                    break
                # Mappatura/arricchimento campo 'titolo'
                for bando in content:
                    titolo = bando.get('titolo') or bando.get('descrizioneBreve') or bando.get('descrizione') or 'Senza titolo'
                    bando['titolo'] = titolo.strip() if titolo else 'Senza titolo'
                    bandi.append(bando)
                print(f"Pagina {page}: {len(content)} bandi trovati")
            except Exception as e:
                print(f"Errore InPA pagina {page}: {e}; risposta: {getattr(r, 'text', '')}")
                break
        return bandi
