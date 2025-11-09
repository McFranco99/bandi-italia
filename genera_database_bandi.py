import json
from datetime import datetime
from inpa_scraper import InPAScraper
from invitalia_scraper import InvitaliaScraper
from mimit_scraper import MIMITScraper
from consap_scraper import ConsapScraper
from gazzetta_scraper import GazzettaScraper

def generate_real_bandi_database():
    bandi = []
    try:
        bandi += InPAScraper().scrape_bandi_list()
        print(f"✅ InPA: {len(bandi)} bandi totali")
    except Exception as e:
        print(f"⚠️ Errore InPA: {e}")

    try:
        bandi += InvitaliaScraper().scrape_incentivi()
        print(f"✅ Invitalia: {len(bandi)} bandi totali")
    except Exception as e:
        print(f"⚠️ Errore Invitalia: {e}")

    try:
        bandi += MIMITScraper().scrape_incentivi()
        print(f"✅ MIMIT: {len(bandi)} bandi totali")
    except Exception as e:
        print(f"⚠️ Errore MIMIT: {e}")

    try:
        bandi += ConsapScraper().scrape()
        print(f"✅ Consap: {len(bandi)} bandi totali")
    except Exception as e:
        print(f"⚠️ Errore Consap: {e}")


    return bandi


def save_to_json():
    bandi = generate_real_bandi_database()
    with open('bandi_database_reale.json', 'w', encoding='utf-8') as f:
        json.dump(bandi, f, ensure_ascii=False)  # senza indentazione

    print(f"💾 File salvato con {len(bandi)} bandi.")


        # 📊 LOG RIEPILOGATIVO
    try:
        print("\n📊 Riepilogo per sorgente:")
        sorgenti = {}
        for bando in bandi:
            src = bando.get("source", "sconosciuta")
            sorgenti[src] = sorgenti.get(src, 0) + 1
        for src, count in sorgenti.items():
            print(f"   - {src}: {count} bandi")
        print("\n✅ Aggiornamento completato con successo.")
    except Exception as e:
        print(f"⚠️ Errore durante il riepilogo: {e}")


if __name__ == "__main__":
    save_to_json()
