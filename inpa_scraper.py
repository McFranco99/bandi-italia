import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

class InPAScraper:
    BASE_URL = "https://www.inpa.gov.it"
    BANDI_URL = f"{BASE_URL}/bandi-e-avvisi/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
        })
    
    def scrape_bandi_list(self, max_pages=1):
        bandi = []
        
        print(f"🔍 Inizio scraping InPA...")
        print(f"   URL: {self.BANDI_URL}\n")
        
        try:
            response = self.session.get(self.BANDI_URL, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cerca varie strutture possibili
            selettori_possibili = [
                ('div', 'card-wrapper'),
                ('div', 'card'),
                ('article', None),
                ('div', 'bando'),
                ('li', 'list-item'),
                ('div', 'risultato'),
                ('a', 'link-list-item')
            ]
            
            bando_elements = []
            for tag, classe in selettori_possibili:
                if classe:
                    elements = soup.find_all(tag, class_=classe)
                else:
                    elements = soup.find_all(tag)
                
                if elements:
                    print(f"✓ Trovati {len(elements)} elementi con <{tag} class='{classe}'>")
                    bando_elements = elements
                    break
            
            if not bando_elements:
                print("⚠️  Nessun elemento trovato con i selettori standard, tento fallback")
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()
                    if ('concorso' in text or 'bando' in text) and len(text) > 20:
                        bando = {
                            'title': link.get_text(strip=True),
                            'category': 'lavoro',
                            'region': 'nazionale',
                            'entity': 'InPA',
                            'description': 'Concorso pubblico',
                            'amount': 0,
                            'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                            'published': datetime.now().strftime('%Y-%m-%d'),
                            'url': f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                            'source': 'inpa'
                        }
                        bandi.append(bando)
                if bandi:
                    print(f"✓ Estratti {len(bandi)} bandi con metodo alternativo")
            else:
                for elem in bando_elements:
                    try:
                        bando = self._parse_bando_element(elem)
                        if bando:
                            bandi.append(bando)
                    except Exception as e:
                        print(f"   ✗ Errore parsing elemento: {str(e)}")
                        continue
            
            # Rimuovi duplicati
            seen = set()
            unique_bandi = []
            for bando in bandi:
                key = bando['title']
                if key not in seen:
                    seen.add(key)
                    unique_bandi.append(bando)
            
            print(f"\n{'='*60}")
            print(f"Totale bandi trovati: {len(unique_bandi)}")
            print(f"{'='*60}\n")
            
            if len(unique_bandi) == 0:
                with open('debug_inpa.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("⚠️  Salvato HTML in 'debug_inpa.html' per debug")
            
            return unique_bandi
            
        except Exception as e:
            print(f"✗ Errore generale scraping InPA: {str(e)}")
            return []
    
    def _parse_bando_element(self, elem):
        try:
            title = None
            for tag in ['h3', 'h4', 'h5', 'a', 'strong']:
                title_elem = elem.find(tag)
                if title_elem and len(title_elem.get_text(strip=True)) > 10:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = elem.get_text(strip=True)[:200]
            
            link = elem.find('a', href=True)
            url = None
            if link:
                href = link.get('href')
                url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
            
            text_content = elem.get_text()
            dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text_content)
            deadline = self._parse_date(dates[-1]) if dates else (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            return {
                'title': title,
                'category': 'lavoro',
                'region': 'nazionale',
                'entity': 'InPA',
                'description': text_content[:300].strip(),
                'amount': 0,
                'deadline': deadline,
                'published': datetime.now().strftime('%Y-%m-%d'),
                'url': url or self.BANDI_URL,
                'source': 'inpa'
            }
        except Exception as e:
            print(f"Errore parsing: {str(e)}")
            return None
    
    def _parse_date(self, date_str):
        try:
            formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except:
            return None


if __name__ == "__main__":
    scraper = InPAScraper()
    bandi = scraper.scrape_bandi_list(max_pages=1)
    if bandi:
        print("✅ Scraping completato con successo!")
        print(f"\nPrimi 3 bandi trovati:")
        for i, bando in enumerate(bandi[:3], 1):
            print(f"\n{i}. {bando['title']}")
            print(f"   Ente: {bando['entity']}")
            print(f"   Scadenza: {bando['deadline']}")
            print(f"   URL: {bando['url']}")
    else:
        print("\n⚠️  Nessun bando trovato")
