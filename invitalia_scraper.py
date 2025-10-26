import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

class InvitaliaScraper:
    BASE = "https://www.invitalia.it"
    ENTRYPOINTS = [
        "/per-chi-vuole-fare-impresa/incentivi-e-strumenti",
        "/per-le-imprese/incentivi-e-strumenti",
        "/per-le-pa/incentivi-e-strumenti",
    ]

    # Indizi che identificano una card di incentivo/bando nella lista
    STATUS_TOKENS = ("attivo", "in apertura", "chiuso", "data apertura", "data chiusura")
    # Evita link testuali di servizio
    TITLE_BLOCK = ("scopri", "seguici", "rimuovi filtri", "cookie", "privacy", "contatti", "newsletter", "news", "eventi")
    HREF_BLOCK  = ("privacy", "cookie", "contatti", "trasparenza", "urp", "newsletter", "login", "accedi", "press", "mappa")
    # Pattern percorsi plausibili per dettagli incentivi/bandi
    PATH_ALLOW  = (r"/incentivi", r"/agevolaz", r"/bando", r"/bandi", r"/misur", r"/finanziam")

    TIMEOUT = 25
    MIN_TITLE = 10
    MIN_SNIPPET = 40

    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update({"User-Agent": "Mozilla/5.0 (BandiItaliaBot/1.0)"})

    def _clean(self, s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip())

    def _is_valid_link(self, url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        u = urlparse(url)
        if "invitalia.it" not in u.netloc:
            return False
        if any(x in url.lower() for x in self.HREF_BLOCK):
            return False
        return any(re.search(p, u.path, re.I) for p in self.PATH_ALLOW)

    def _has_status_tokens(self, text: str) -> bool:
        low = (text or "").lower()
        return any(tok in low for tok in self.STATUS_TOKENS)

    def _parse_dates(self, text: str) -> tuple[str | None, str | None]:
        # dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
        open_dt = close_dt = None
        if not text:
            return None, None
        low = text.lower()
        dates = re.findall(r"\b(\d{2}[\/\.\-]\d{2}[\/\.\-]\d{4})\b", text)
        if "data apertura" in low or "in apertura" in low:
            open_dt = dates[0] if dates else None
        if "data chiusura" in low or "chius" in low:
            # prendi l’ultima come chiusura se ce ne sono due
            close_dt = dates[-1] if len(dates) else None
        # fallback: se c’è una sola data e non c’è “chiusura”, usala come apertura
        if not open_dt and dates:
            open_dt = dates[0]
        return open_dt, close_dt

    def _extract_snippet(self, card) -> str:
        # usa <p> della card o testo dei figli, evitando bottoni
        texts = []
        for p in card.select("p, .teaser__text, .card__text"):
            t = self._clean(p.get_text(" ", strip=True))
            if t and not t.lower().startswith(("scopri", "segui")):
                texts.append(t)
        if not texts:
            t = self._clean(card.get_text(" ", strip=True))
            texts = [t]
        snippet = self._clean(" ".join(texts))
        return snippet[:600]

    def _extract_title(self, card) -> str:
        title_el = card.select_one("h2, h3, .card__title, .teaser__title, a")
        return self._clean(title_el.get_text(" ", strip=True) if title_el else "")

    def _find_next_page(self, soup, current_url: str) -> str | None:
        # prova <a rel="next">, aria-label, o “successiva”
        a = soup.select_one("a[rel='next']")
        if a and a.get("href"):
            return urljoin(current_url, a["href"])
        for cand in soup.select("a[href]"):
            txt = self._clean(cand.get_text(" ", strip=True)).lower()
            aria = (cand.get("aria-label") or "").lower()
            if "successiv" in txt or "successiv" in aria or "pagina successiva" in aria:
                return urljoin(current_url, cand.get("href"))
        # fallback: link con ?page= o &page=
        for cand in soup.select("a[href*='page=']"):
            return urljoin(current_url, cand.get("href"))
        return None

    def _extract_cards_from_listing(self, soup, base_url: str) -> list[dict]:
        results = []
        # blocchi tipici di card/teaser/list-item
        blocks = soup.select("article, .card, .teaser, li, .list-item")
        for b in blocks:
            # per essere card incentivo: deve avere token di stato o “data apertura/chiusura”
            raw_text = self._clean(b.get_text(" ", strip=True))
            if not self._has_status_tokens(raw_text):
                continue
            # titolo e link
            title = self._extract_title(b)
            if len(title) < self.MIN_TITLE or any(x in title.lower() for x in self.TITLE_BLOCK):
                continue
            a = b.select_one("a[href]")
            if not a:
                continue
            href = a.get("href", "")
            link = href if href.startswith("http") else urljoin(base_url, href)
            if not self._is_valid_link(link):
                continue
            # snippet e date
            snippet = self._extract_snippet(b)
            if len(snippet) < self.MIN_SNIPPET:
                # se snippet è corto, prova a prendere testo dei primi <p> globali
                ps = soup.select("main p, article p")
                if ps:
                    snippet = self._clean(" ".join(p.get_text(" ", strip=True) for p in ps[:3]))[:600]
            open_dt, close_dt = self._parse_dates(raw_text)
            deadline = close_dt or open_dt or "A sportello"
            # stato
            status = "aperto"
            low = raw_text.lower()
            if "in apertura" in low:
                status = "scadenza"
            elif "chiuso" in low:
                status = "chiuso"

            results.append({
                "id": abs(hash(link)),
                "title": title,
                "category": "imprese",
                "region": "nazionale",
                "entity": "Invitalia",
                "description": snippet,
                "amount": 0,
                "deadline": deadline,
                "published": datetime.utcnow().strftime("%Y-%m-%d"),
                "url": link,
                "source": "invitalia",
                "status": status
            })
        return results

    def scrape_listing(self, start_url: str, max_pages: int = 30, sleep_sec: float = 0.5) -> list[dict]:
        out, seen = [], set()
        url = start_url
        pages = 0
        while url and pages < max_pages:
            r = self.sess.get(url, timeout=self.TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            items = self._extract_cards_from_listing(soup, url)
            for it in items:
                k = it["url"]
                if k in seen:
                    continue
                seen.add(k)
                out.append(it)
            next_url = self._find_next_page(soup, url)
            url = next_url
            pages += 1
            time.sleep(sleep_sec)
        return out

    def scrape_incentivi(self, max_pages_per_list: int = 30) -> list[dict]:
        all_items = []
        for ep in self.ENTRYPOINTS:
            url = urljoin(self.BASE, ep)
            items = self.scrape_listing(url, max_pages=max_pages_per_list)
            all_items.extend(items)
        # dedup finale per URL
        dedup, seen = [], set()
        for r in all_items:
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            dedup.append(r)
        print(f"Invitalia: {len(all_items)} trovati, {len(dedup)} unici")
        return dedup

if __name__ == "__main__":
    s = InvitaliaScraper()
    data = s.scrape_incentivi()
    print("Esempi:", len(data))
    for d in data[:10]:
        print(d["status"], "|", d["deadline"], "|", d["title"], "->", d["url"])
