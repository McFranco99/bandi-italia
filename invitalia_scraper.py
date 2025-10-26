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

                # Card/link a strumenti e incentivi (adatta il selettore secondo la pagina)
                links = soup.select("a[href^='/incentivi-e-strumenti'], a[href^='/per-chi-vuole-fare-impresa/'], a[href^='/per-le-imprese/'], a[href^='/per-le-pa/']")
                found = set()
                for link in links:
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    if not href or len(title) < 8:
                        continue
                    if not href.startswith("http"):
                        href = self.base_url + href
                    key = (title, href)
                    if key in found:
                        continue
                    found.add(key)
                    bando = {
                        'id': abs(hash(title+href)),
                        'title': title,
                        'category': 'investimenti',
                        'region': 'nazionale',
                        'entity': 'Invitalia',
                        'description': '',
                        'amount': 0,
                        'deadline': None,
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'url': href,
                        'source': 'invitalia'
                    }
                    bandi.append(bando)
            except Exception as e:
                print(f"❌ Errore scraping {url}: {e}")

        print(f"✅ Invitalia: {len(bandi)} bandi/incentivi trovati")
        return bandi

if __name__ == '__main__':
    scraper = InvitaliaScraper()
    bandi = scraper.scrape_incentivi()
    print(f"\nTotale bandi/incentivi: {len(bandi)}")
    for bando in bandi[:10]:
        print(f"- {bando['title']} ({bando['url']})")
