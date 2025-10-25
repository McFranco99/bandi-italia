"""
Main Scraper - Orchestra tutti gli scraper e salva in database
"""

from scrapers.inpa_scraper import InPAScraper
from scrapers.invitalia_scraper import InvitaliaScraper
from scrapers.gazzetta_scraper import GazzettaScraper
from database import Database
from datetime import datetime
import schedule
import time
import json

class MasterScraper:
    def __init__(self):
        self.db = Database()
        self.scrapers = {
            'inpa': InPAScraper(),
            'invitalia': InvitaliaScraper(),
            'gazzetta': GazzettaScraper()
        }
    
    def run_all_scrapers(self):
        """Esegui tutti gli scraper"""
        print(f"\n{'='*70}")
        print(f"🔄 Avvio scraping automatico - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        all_bandi = []
        
        # 1. Scrape InPA
        print("📡 Scraping InPA...")
        try:
            inpa_bandi = self.scrapers['inpa'].scrape_bandi_list(max_pages=3)
            all_bandi.extend(inpa_bandi)
            print(f"✓ InPA: {len(inpa_bandi)} bandi trovati\n")
        except Exception as e:
            print(f"✗ Errore InPA: {str(e)}\n")
        
        # 2. Scrape Invitalia
        print("📡 Scraping Invitalia...")
        try:
            invitalia_bandi = self.scrapers['invitalia'].scrape_all_bandi()
            all_bandi.extend(invitalia_bandi)
            print(f"✓ Invitalia: {len(invitalia_bandi)} bandi trovati\n")
        except Exception as e:
            print(f"✗ Errore Invitalia: {str(e)}\n")
        
        # 3. Scrape Gazzetta Ufficiale
        print("📡 Scraping Gazzetta Ufficiale...")
        try:
            gazzetta_bandi = self.scrapers['gazzetta'].scrape_recent_concorsi()
            all_bandi.extend(gazzetta_bandi)
            print(f"✓ Gazzetta: {len(gazzetta_bandi)} bandi trovati\n")
        except Exception as e:
            print(f"✗ Errore Gazzetta: {str(e)}\n")
        
        # Salva in database
        print(f"💾 Salvataggio {len(all_bandi)} bandi in database...")
        new_bandi_count = self.db.save_bandi(all_bandi)
        
        print(f"\n{'='*70}")
        print(f"✅ Scraping completato!")
        print(f"   Totale bandi trovati: {len(all_bandi)}")
        print(f"   Nuovi bandi aggiunti: {new_bandi_count}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        return all_bandi
    
    def schedule_scraping(self):
        """Programma scraping automatico ogni 6 ore"""
        # Esegui immediatamente
        self.run_all_scrapers()
        
        # Programma esecuzioni future
        schedule.every(6).hours.do(self.run_all_scrapers)
        
        print("⏰ Scraping programmato ogni 6 ore")
        print("   Premi Ctrl+C per fermare\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    scraper = MasterScraper()
    
    # Opzione 1: Esegui una volta
    # scraper.run_all_scrapers()
    
    # Opzione 2: Esegui continuamente (cron job)
    scraper.schedule_scraping()
