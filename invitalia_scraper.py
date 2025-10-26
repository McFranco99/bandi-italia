import requests
from bs4 import BeautifulSoup
from datetime import datetime

class InvitaliaScraper:
    def __init__(self):
        self.base_url = "https://www.invitalia.it"
        self.entrypoints = [
            "/per-chi-vuole-fare-impresa/incentivi-e-strumenti",
            "/per-le-imprese/incentivi-e-strumenti",
            "/per-le-pa/incentivi-e-strumenti"
        ]

    def scrape_incentivi(self):
        print("🔍 Inizio scraping Invitalia macroaree incentivi...")
        bandi = []
        for page in self.entrypoints:
            url = self.base_url + page
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                # cerca tutti i link a bandi/progetti/strumenti almeno un po' descrittivi
                links = soup.select("a[href^='/']")
                found = set()
                for link in links:
                    titolo = link.get_text(strip=True)
                    href = link.get("href", "")
                    # punta a sottopagine del sito e taglia titoli social/navigation/useless
                    if not href or len(titolo) < 8: continue
                    if href.startswith("/chi-siamo") or href.startswith("/contatti"): continue
                    full_url = href if href.startswith("http") else self.base_url + href
                    key = (titolo, full_url)
                    if key in found: continue
                    found.add(key)
                    # ora si approfondisce la pagina dettaglio
                    dettagli = self.scrape_dettaglio(full_url)
                    bando = {
                        'id': abs(hash(full_url+titolo)),
                        'title': titolo,
                        'category': dettagli.get("category", "investimenti"),
                        'region': 'nazionale',
                        'entity': 'Invitalia',
                        'description': dettagli.get("descrizione",''),
                        'amount': 0,
                        'deadline': dettagli.get("scadenza", None),
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'url': full_url,
                        'source': 'invitalia'
                    }
                    bandi.append(bando)
            except Exception as e:
                print(f"❌ Errore scraping {url}: {e}")

        print(f"✅ Invitalia: {len(bandi)} bandi/incentivi trovati")
        return bandi

    def scrape_dettaglio(self, url):
        result = {"descrizione":''}
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            s = BeautifulSoup(r.content, 'html.parser')
            # descrizione lunga
            desc = ""
            for par in s.find_all(['p','li']):
                t = par.get_text(strip=True)
                # filtra solo paragrafi abbastanza lunghi e informativi
                if t and len(t) > 30 and not t.startswith('Seguici') and not t.startswith('Scarica'):
                    desc += t + "\n"
            result["descrizione"] = desc[:600].replace('\n', ' ')
            # prova estrazione data scadenza cercando un pattern classico
            for par in s.find_all(text=True):
                if 'scad' in par.lower():
                    # es: 'Scadenza presentazione domande: 05/03/2026'
                    for part in par.replace(':', ' ').split():
                        if '/' in part and len(part) == 10:
                            result["scadenza"] = part
            # prova categorizzazione
            if '/tasso-zero' in url or 'nuove-imprese' in url:
                result['category'] = 'startup'
            elif 'fondo' in url:
                result['category'] = 'investimenti'
            elif 'casa' in url or 'immobile' in url:
                result['category'] = 'immobili'
        except Exception as e:
            result["descrizione"] = ''
        return result

if __name__ == '__main__':
    scraper = InvitaliaScraper()
    bandi = scraper.scrape_incentivi()
    print(f"\n✅ Totale bandi Invitalia: {len(bandi)}")
    for b in bandi[:10]:
        print(f"{b['title']} | {b['category']} | {b['url']}")
