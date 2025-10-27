import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

class ConsapDynamicScraper:
    def __init__(self):
        self.base_url = "https://www.consap.it/"
        self.source = "Consap"

    def scrape(self):
        bandi = []
        try:
            print("[ConsapDynamicScraper] Avvio scraping dinamico...")

            r = requests.get(self.base_url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # 🔍 Trova tutti i link assoluti relativi a Consap
            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                # Filtra solo link del dominio consap.it e di livello "bando"
                if href.startswith("/"):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith("https://www.consap.it/"):
                    full_url = href
                else:
                    continue

                # Escludi sezioni generiche o di servizio
                path = urlparse(full_url).path.strip("/")
                if not path or any(x in path for x in [
                    "chi-siamo", "media-room", "contatti", "privacy", "cookie", "home", "servizi"
                ]):
                    continue

                # Accetta solo URL di tipo /fondo-.../, /bonus-.../, /indennizzo-.../, ecc.
                if any(path.startswith(prefix) for prefix in [
                    "fondo-", "bonus-", "indennizzo-", "ricostruzione-", "sisma-", "garanzia-", "sostegno-"
                ]):
                    links.add(full_url)

            print(f"[ConsapDynamicScraper] Trovati {len(links)} link potenziali di bandi Consap.")

            # 🔁 Visita ogni link e raccoglie i dati
            for url in links:
                try:
                    sub = requests.get(url, timeout=10)
                    sub.raise_for_status()
                    subsoup = BeautifulSoup(sub.text, "html.parser")

                    titolo = (subsoup.find("h1") or subsoup.find("title") or "").get_text(strip=True)
                    content_block = subsoup.find("div", class_="content") or subsoup
                    descrizione = content_block.get_text(" ", strip=True)[:900]

                    # Stima la categoria in base al titolo
                    titolo_lower = titolo.lower()
                    if any(x in titolo_lower for x in ["impresa", "imprese", "azienda"]):
                        categoria = "imprese"
                    elif any(x in titolo_lower for x in ["casa", "mutuo", "immobile", "abitazione"]):
                        categoria = "immobili"
                    elif any(x in titolo_lower for x in ["studio", "natalità", "famiglia", "sostegno"]):
                        categoria = "generale"
                    else:
                        categoria = "generale"

                    bando = {
                        "titolo": titolo or "Bando Consap",
                        "descrizione": descrizione or "Nessuna descrizione disponibile.",
                        "ente": self.source,
                        "categoria": categoria,
                        "regione": "nazionale",
                        "stato": "aperto",
                        "importo": 0,
                        "scadenza": "N/D",
                        "link": url
                    }
                    bandi.append(bando)
                except Exception as sub_e:
                    print(f"[ConsapDynamicScraper] Errore nel parsing di {url}: {sub_e}")

            print(f"[ConsapDynamicScraper] ✅ Trovati {len(bandi)} bandi validi Consap.")
            return bandi

        except Exception as e:
            print(f"[ConsapDynamicScraper] ❌ Errore principale: {e}")
            return []
