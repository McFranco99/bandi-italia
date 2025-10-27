import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

class ConsapScraper:
    def __init__(self):
        self.base_url = "https://www.consap.it/"
        self.source = "Consap"

    def scrape(self):
        bandi = []
        try:
            print("[ConsapScraper] 🔍 Avvio scraping Consap dinamico...")

            r = requests.get(self.base_url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()

                # normalizza URL relativi
                if href.startswith("/"):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith("https://www.consap.it/"):
                    full_url = href
                else:
                    continue

                path = urlparse(full_url).path.strip("/")

                # ignora pagine istituzionali, tiene solo i fondi
                if not path or any(x in path for x in [
                    "chi-siamo", "media-room", "contatti", "privacy", "cookie", "servizi",
                    "news", "comunicati-stampa", "dicono-di-noi"
                ]):
                    continue

                if any(path.startswith(prefix) for prefix in [
                    "fondo-", "bonus-", "indennizzo-", "sostegno-", "sisma-", "garanzia-", "ricostruzione-"
                ]):
                    links.add(full_url)

            print(f"[ConsapScraper] 🌐 Trovati {len(links)} link potenziali.")

            for url in links:
                try:
                    sub = requests.get(url, timeout=10)
                    sub.raise_for_status()
                    subsoup = BeautifulSoup(sub.text, "html.parser")

                    titolo = (subsoup.find("h1") or subsoup.find("title")).get_text(strip=True)
                    content = subsoup.find("div", class_="content") or subsoup
                    descrizione = content.get_text(" ", strip=True)[:800]

                    titolo_lower = titolo.lower()
                    if any(x in titolo_lower for x in ["casa", "mutuo", "immobile"]):
                        categoria = "immobili"
                    elif any(x in titolo_lower for x in ["impresa", "azienda"]):
                        categoria = "imprese"
                    else:
                        categoria = "generale"

                    bando = {
                        "titolo": titolo,
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
                    print(f"[ConsapScraper] ⚠️ Errore parsing {url}: {sub_e}")

            print(f"[ConsapScraper] ✅ Raccolti {len(bandi)} bandi Consap.")
            return bandi

        except Exception as e:
            print(f"[ConsapScraper] ❌ Errore principale: {e}")
            return []
