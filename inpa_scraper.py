import requests
import time
import json

BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
PAGE_SIZE = 50

def get_all_bandi():
    page = 0
    bandi = []
    while True:
        url = f"{BASE_URL}?page={page}&size={PAGE_SIZE}"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            content = data.get("content", [])
            if not content:
                break
            bandi.extend(content)
            print(f"Pagina {page}: {len(content)} bandi trovati")
            page += 1
            time.sleep(1)  # evita sovraccarico server
        except Exception as e:
            print(f"Errore fetching pagina {page}: {e}")
            break

    print(f"Totale bandi trovati: {len(bandi)}")
    return bandi

if __name__ == "__main__":
    bandi = get_all_bandi()
    with open("bandi_inpa.json", "w", encoding="utf-8") as f:
        json.dump(bandi, f, ensure_ascii=False, indent=2)
    print(f"Salvati {len(bandi)} bandi in 'bandi_inpa.json'")
