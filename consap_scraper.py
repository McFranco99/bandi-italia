import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re


def normalizza_categoria(categoria):
    """Uniforma la categoria in una delle 4 principali."""
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


def estrai_info_chiave(testo):
    """Cerca importo, scadenza e altre info nel testo."""
    info = {
        "importo": 0,
        "scadenza": "N/D",
        "regione": "Nazionale",
    }

    # Importo (es. 250.000 euro)
    match_importo = re.search(r"(\d[\d\.\,]{2,})\s*(euro|€)", testo, re.IGNORECASE)
    if match_importo:
        try:
            valore = match_importo.group(1).replace(".", "").replace(",", ".")
            info["importo"] = float(valore)
        except:
            pass

    # Scadenza (es. 31 dicembre 2027)
    match_scad = re.search(r"(\d{1,2}\s+[a-zàéìòù]+\s+\d{4})", testo, re.IGNORECASE)
    if match_scad:
        data_str = match_scad.group(1)
        try:
            info["scadenza"] = datetime.strptime(data_str, "%d %B %Y").strftime("%Y-%m-%d")
        except:
            info["scadenza"] = data_str

    # Regione (se menzionata)
    if re.search(r"nazional", testo, re.IGNORECASE):
        info["regione"] = "nazionale"
    elif re.search(r"regione\s+([A-Z][a-z]+)", testo):
        regione_match = re.search(r"regione\s+([A-Z][a-z]+)", testo)
        info["regione"] = regione_match.group(1)

    return info


class ConsapScraper:
    def __init__(self):
        self.start_urls = [
            "https://www.consap.it/servizi-assicurativi/",
            "https://www.consap.it/servizi-di-sostegno/",
            "https://www.consap.it/servizi-finanziari/"
        ]
        self.source = "Consap"

    def scrape(self):
        bandi = []
        try:
            print("[ConsapScraper] 🔍 Avvio scraping Consap...")

            links = set()

            # 1️⃣ Trova i link ai fondi
            for start_url in self.start_urls:
                try:
                    r = requests.get(start_url, timeout=10)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")

                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()

                        if href.startswith("/"):
                            full_url = urljoin(start_url, href)
                        elif href.startswith("https://www.consap.it/"):
                            full_url = href
                        else:
                            continue

                        path = urlparse(full_url).path.strip("/")
                        if not path or any(x in path for x in [
                            "chi-siamo", "media-room", "contatti", "privacy", "cookie",
                            "news", "comunicati", "istituzionale", "video"
                        ]):
                            continue

                        if any(path.startswith(prefix) for prefix in [
                            "fondo-", "bonus-", "indennizzo-", "sostegno-", "sisma-", "garanzia-", "ricostruzione-", "buono-", "carta-"
                        ]):
                            links.add(full_url)

                except Exception as e:
                    print(f"[ConsapScraper] ⚠️ Errore sezione {start_url}: {e}")

            print(f"[ConsapScraper] 🌐 Trovati {len(links)} link da Consap.")

            # 2️⃣ Analizza ogni bando
            for url in sorted(list(links)):
                try:
                    sub = requests.get(url, timeout=10)
                    sub.raise_for_status()
                    subsoup = BeautifulSoup(sub.text, "html.parser")

                    titolo_tag = subsoup.find("h1") or subsoup.find("title")
                    titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Bando Consap"
                    titolo_lower = titolo.lower()

                    if any(x in titolo_lower for x in ["media room", "video", "comunicato", "istituzionale"]):
                        continue

                    # Corpo principale
                    content = subsoup.find("div", class_="single-content") or subsoup.find("main") or subsoup
                    testo = content.get_text(" ", strip=True)

                    # Sezioni aggiuntive
                    extra_sections = []
                    for h2 in subsoup.find_all(["h2", "h3"]):
                        titolo_sezione = h2.get_text(strip=True)
                        next_div = h2.find_next("div")
                        if next_div:
                            paragrafo = next_div.get_text(" ", strip=True)
                            if paragrafo:
                                extra_sections.append(f"\n\n{titolo_sezione.upper()}\n{paragrafo}")

                    testo_completo = testo + "\n" + "\n".join(extra_sections)
                    testo_completo = re.sub(r"\s+", " ", testo_completo).strip()

                    # 🔎 Stato
                    testo_lower = testo_completo.lower()
                    if any(kw in testo_lower for kw in ["non è più possibile", "chiuso", "cessato"]):
                        stato = "chiuso"
                    else:
                        stato = "aperto"

                    # 🔍 Estrazione dati strutturati
                    info = estrai_info_chiave(testo_completo)

                    # 🔖 Categoria
                    if any(x in titolo_lower for x in ["casa", "mutuo", "immobile"]):
                        categoria = "immobili"
                    elif any(x in titolo_lower for x in ["impresa", "azienda", "ecologica"]):
                        categoria = "imprese"
                    elif any(x in titolo_lower for x in ["bonus", "studio", "docente", "patente"]):
                        categoria = "lavoro"
                    else:
                        categoria = "generale"

                    categoria = normalizza_categoria(categoria)

                    bando = {
                        "titolo": titolo,
                        "descrizione": testo_completo[:1800],
                        "ente": self.source,
                        "categoria": categoria,
                        "regione": info["regione"].capitalize(),
                        "stato": stato,
                        "importo": info["importo"],
                        "scadenza": info["scadenza"],
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
