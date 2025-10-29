import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import json
import os


def normalizza_categoria(categoria):
    """
    Uniforma la categoria in una delle 4 principali:
    'immobili', 'imprese', 'lavoro', 'generale'.
    """
    if not categoria:
        return "generale"
    cat = categoria.lower().strip()
    if "lavor" in cat or "concors" in cat:
        return "lavoro"
    if "impres" in cat or "invest" in cat:
        return "imprese"
    if "immobil" in cat or "casa" in cat or "mutuo" in cat:
        return "immobili"
    return "generale"


class ConsapScraper:
    def __init__(self):
        self.start_urls = [
            "https://www.consap.it/servizi-assicurativi/",
            "https://www.consap.it/servizi-di-sostegno/",
            "https://www.consap.it/servizi-finanziari/"
        ]
        self.source = "Consap"
        self.manual_file = "data/manual_overrides.json"  # ✅ file per descrizioni/modifiche manuali

    def carica_modifiche_manual(self):
        """Carica eventuali descrizioni brevi o dati aggiornati manualmente."""
        if os.path.exists(self.manual_file):
            try:
                with open(self.manual_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ConsapScraper] ⚠️ Errore lettura file manual_overrides.json: {e}")
        return {}

    def scrape(self):
        bandi = []
        manual_data = self.carica_modifiche_manual()

        try:
            print("[ConsapScraper] 🔍 Avvio scraping Consap...")

            links = set()

            # 1️⃣ Scansione sezioni principali per trovare tutti i fondi
            for start_url in self.start_urls:
                try:
                    r = requests.get(start_url, timeout=10)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")

                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()

                        # normalizza URL
                        if href.startswith("/"):
                            full_url = urljoin(start_url, href)
                        elif href.startswith("https://www.consap.it/"):
                            full_url = href
                        else:
                            continue

                        path = urlparse(full_url).path.strip("/")

                        # ignora pagine non rilevanti
                        if not path or any(x in path for x in [
                            "chi-siamo", "media-room", "contatti", "privacy", "cookie",
                            "news", "comunicati", "istituzionale", "video"
                        ]):
                            continue

                        # tieni solo pagine con fondi o bonus
                        if any(path.startswith(prefix) for prefix in [
                            "fondo-", "bonus-", "indennizzo-", "sostegno-", "sisma-", "garanzia-",
                            "ricostruzione-", "buono-", "carta-"
                        ]):
                            links.add(full_url)
                except Exception as e:
                    print(f"[ConsapScraper] ⚠️ Errore su sezione {start_url}: {e}")

            print(f"[ConsapScraper] 🌐 Trovati {len(links)} link potenziali da Consap.")

            # 2️⃣ Analizza ogni fondo trovato
            for url in sorted(list(links)):
                try:
                    sub = requests.get(url, timeout=10)
                    sub.raise_for_status()
                    subsoup = BeautifulSoup(sub.text, "html.parser")

                    # titolo principale
                    titolo_tag = subsoup.find("h1") or subsoup.find("title")
                    titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Bando Consap"
                    titolo_lower = titolo.lower()

                    # ignora pagine inutili
                    if any(x in titolo_lower for x in ["media room", "video", "comunicato", "istituzionale"]):
                        continue

                    # corpo testo vero (sezione centrale)
                    content = subsoup.find("div", class_="single-content") or subsoup.find("main") or subsoup
                    testo = content.get_text(" ", strip=True)
                    testo = re.sub(r"(Chi siamo|Media Room|Contatti|Servizi|Certificazioni|Ruolo dei periti|Centro di Informazione|Organismo di Indennizzo)[^.]*", "", testo)
                    testo = re.sub(r"\s+", " ", testo).strip()

                    # stato del fondo (aperto/chiuso)
                    testo_lower = testo.lower()
                    if any(kw in testo_lower for kw in [
                        "non è più possibile presentare domanda",
                        "fondo abrogato",
                        "non è più attivo",
                        "chiuso",
                        "cessato"
                    ]):
                        stato = "chiuso"
                    else:
                        stato = "aperto"

                    descrizione = testo[:800] if testo else "Nessuna descrizione disponibile."

                    # categorizzazione coerente con BandiPerTe
                    if any(x in titolo_lower for x in ["casa", "mutuo", "immobile"]):
                        categoria = "immobili"
                    elif any(x in titolo_lower for x in ["impresa", "azienda", "autotrasporto", "ecologica"]):
                        categoria = "imprese e investimenti"
                    elif any(x in titolo_lower for x in ["bonus", "cultura", "studio", "docente", "vista", "patente"]):
                        categoria = "lavoro e concorsi"
                    else:
                        categoria = "generale"

                    categoria = normalizza_categoria(categoria)

                    # 🔄 Applica eventuali modifiche manuali (descrizione breve, importo, scadenza ecc.)
                    override = manual_data.get(titolo) or manual_data.get(url) or {}

                    bando = {
                        "titolo": titolo,
                        "descrizione": descrizione,
                        "descrizione_breve": override.get("descrizione_breve", ""),  # ✍️ testo editoriale manuale
                        "ente": self.source,
                        "categoria": categoria,
                        "regione": "Nazionale",
                        "stato": stato,
                        "importo": override.get("importo", 0),
                        "scadenza": override.get("scadenza", "N/D"),
                        "link": url
                    }

                    bandi.append(bando)

                except Exception as sub_e:
                    print(f"[ConsapScraper] ⚠️ Errore parsing {url}: {sub_e}")

            print(f"[ConsapScraper] ✅ Raccolti {len(bandi)} bandi Consap validi.")
            return bandi

        except Exception as e:
            print(f"[ConsapScraper] ❌ Errore principale: {e}")
            return []
