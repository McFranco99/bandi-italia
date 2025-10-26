from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time
import sys

# ========================
# 🔧 CONFIGURAZIONE BASE
# ========================

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Scraper disponibili
try:
    from inpa_scraper import InPAScraper
    INPA_AVAILABLE = True
except Exception as e:
    INPA_AVAILABLE = False
    print(f"⚠️ InPAScraper non disponibile: {e}")

try:
    from gazzetta_scraper import GazzettaScraper
    GAZZETTA_AVAILABLE = True
except Exception as e:
    GAZZETTA_AVAILABLE = False
    print(f"⚠️ GazzettaScraper non disponibile: {e}")

try:
    from mimit_scraper import MIMITScraper
    MIMIT_AVAILABLE = True
except Exception as e:
    MIMIT_AVAILABLE = False
    print(f"⚠️ MIMITScraper non disponibile: {e}")

try:
    from invitalia_scraper import InvitaliaScraper
    INVITALIA_AVAILABLE = True
except Exception as e:
    INVITALIA_AVAILABLE = False
    print(f"⚠️ InvitaliaScraper non disponibile: {e}")

# ========================
# 🚀 INIZIALIZZAZIONE APP
# ========================

app = Flask(__name__)
from flask import redirect, request

@app.before_request
def force_https_and_www():
    url = request.url
    if not request.is_secure or not request.host.startswith("www."):
        secure_url = url.replace("http://", "https://")
        if not request.host.startswith("www."):
            secure_url = secure_url.replace(request.host, f"www.{request.host}")
        return redirect(secure_url, code=301)
CORS(app)

bandi_cache = []
ultimo_aggiornamento = None
JSON_FILE = "bandi_database_reale.json"


# ========================
# 🧠 FUNZIONI DI UTILITÀ
# ========================

def carica_bandi_da_json():
    """Carica i bandi da file JSON se esiste"""
    global bandi_cache
    try:
        if not os.path.exists(JSON_FILE):
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"📁 Creato file JSON vuoto: {JSON_FILE}")
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            bandi_cache = json.load(f)
        print(f"✅ Caricati {len(bandi_cache)} bandi da {JSON_FILE}")
        return True
    except Exception as e:
        print(f"⚠️ Errore caricamento JSON: {e}")
        return False


def salva_bandi_su_json():
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(bandi_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvati {len(bandi_cache)} bandi su {JSON_FILE}")
    except Exception as e:
        print(f"⚠️ Errore salvataggio JSON: {e}")


def aggiungi_bando(nuovo_bando):
    global bandi_cache
    if not any(b.get("url") == nuovo_bando.get("url") for b in bandi_cache):
        bandi_cache.append(nuovo_bando)
        return True
    return False


# ========================
# 🤖 SCRAPING AUTOMATICO
# ========================

def aggiorna_bandi_background():
    global bandi_cache, ultimo_aggiornamento

    while True:
        try:
            print(f"\n{'=' * 70}")
            print(f"🔄 Avvio scraping automatico - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 70}\n")

            nuovi_bandi_temp = []

            # InPA
            if INPA_AVAILABLE:
                try:
                    scraper = InPAScraper()
                    nuovi_bandi_temp += scraper.scrape_bandi_list(max_pages=3)
                    print(f"✅ InPA: {len(nuovi_bandi_temp)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping InPA: {e}")

            # Gazzetta
            if GAZZETTA_AVAILABLE:
                try:
                    scraper = GazzettaScraper()
                    nuovi_bandi_temp += scraper.scrape_ultimi_30_giorni()
                    print(f"✅ Gazzetta: {len(nuovi_bandi_temp)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping Gazzetta: {e}")

            # MIMIT
            if MIMIT_AVAILABLE:
                try:
                    scraper = MIMITScraper()
                    nuovi_bandi_temp += scraper.scrape_incentivi()
                    print(f"✅ MIMIT: {len(nuovi_bandi_temp)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping MIMIT: {e}")

            # Invitalia
            if INVITALIA_AVAILABLE:
                try:
                    scraper = InvitaliaScraper()
                    nuovi_bandi_temp += scraper.scrape_incentivi()
                    print(f"✅ Invitalia: {len(nuovi_bandi_temp)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping Invitalia: {e}")

            # Aggiorna cache
            if nuovi_bandi_temp:
                bandi_cache[:] = nuovi_bandi_temp
                salva_bandi_su_json()
                ultimo_aggiornamento = datetime.now()
                print(f"✅ Cache aggiornata con {len(bandi_cache)} bandi totali")
            else:
                print("⚠️ Nessun bando recuperato")

            print(f"⏰ Prossimo aggiornamento tra 30 minuti\n{'=' * 70}\n")

        except Exception as e:
            print(f"❌ Errore generale scraping: {str(e)}")

        time.sleep(30 * 60)


def avvia_scraping_iniziale():
    print("📡 Caricamento bandi iniziale...")
    if carica_bandi_da_json():
        print(f"✅ Bandi iniziali caricati: {len(bandi_cache)}")
    else:
        print("⚠️ Nessun bando iniziale trovato")


def avvia_thread_scraping():
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()


# ========================
# 🌐 ENDPOINT API
# ========================

@app.route("/")
def serve_frontend():
    return send_from_directory(".", "index.html")


@app.route("/api/bandi")
def get_bandi():
    return jsonify({
        "success": True,
        "count": len(bandi_cache),
        "ultimo_aggiornamento": ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        "bandi": bandi_cache
    })


@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "ok",
        "bandi_count": len(bandi_cache),
        "ultimo_aggiornamento": ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        "scrapers_disponibili": {
            "inpa": INPA_AVAILABLE,
            "gazzetta": GAZZETTA_AVAILABLE,
            "mimit": MIMIT_AVAILABLE,
            "invitalia": INVITALIA_AVAILABLE
        }
    })


# ========================
# 🚀 AVVIO AUTOMATICO PER RAILWAY
# ========================

try:
    print("⚙️ Avvio automatico di scraping iniziale e thread background...")
    avvia_scraping_iniziale()
    avvia_thread_scraping()
except Exception as e:
    print(f"❌ Errore in avvio automatico: {e}")

# Solo per esecuzione locale
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Esecuzione locale su porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
