import requests

BASE_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
PAGE_SIZE = 50  # puoi aumentare fino a 100 se il server lo accetta

def get_all_bandi():
    page = 0
    bandi = []
    while True:
        url = f"{BASE_URL}?page={page}&size={PAGE_SIZE}"
        r = requests.get(url)
        data = r.json()
        content = data.get("content", [])
        if not content:
            break
        bandi.extend(content)
        print(f"Pagina {page}: {len(content)} bandi trovati")
        page += 1
    print(f"Totale bandi trovati: {len(bandi)}")
    return bandi

if __name__ == "__main__":
    bandi = get_all_bandi()
    # Fai qualcosa con la lista, per esempio stampa i primi titoli:
    for b in bandi[:10]:
        print(b.get("oggetto", ""), "-", b.get("ente", ""), "-", b.get("dataScadenza", ""))
