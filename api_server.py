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

# @app.before_request
# def force_https_and_www():
#     forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
#     host = request.host

#     # forza HTTPS solo se non già in https
#     if forwarded_proto != "https":
#         secure_url = request.url.replace("http://", "https://")
#         return redirect(secure_url, code=301)

#     # forza www solo se mancante
#     if not host.startswith("www."):
#         secure_url = request.url.replace(host, f"www.{host}")
#         return redirect(secure_url, code=301)


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
# 🗺️ SITEMAP & ROBOTS
# ========================

from flask import send_from_directory

@app.route("/sitemap.xml")
def serve_sitemap():
    """Serve la sitemap XML per Google"""
    return send_from_directory(os.getcwd(), "sitemap.xml")

@app.route("/robots.txt")
def serve_robots():
    """Serve il file robots.txt"""
    return send_from_directory(os.getcwd(), "robots.txt")

@app.route("/ads.txt")
def serve_ads():
    """Serve il file ads.txt per Google AdSense"""
    return send_from_directory(os.getcwd(), "ads.txt")


# ========================
# 🚀 AVVIO AUTOMATICO PER RAILWAY
# ========================

try:
    print("⚙️ Avvio automatico di scraping iniziale e thread background...")
    avvia_scraping_iniziale()
    avvia_thread_scraping()
except Exception as e:
    print(f"❌ Errore in avvio automatico: {e}")

@app.route("/<path:path>")
def serve_static_files(path):
    """Serve tutti i file statici dalla root (per AdSense, sitemap, robots, ecc.)"""
    return send_from_directory(".", path)

# Solo per esecuzione locale
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Esecuzione locale su porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
