from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import threading
import subprocess
from datetime import datetime

# ========================
# 🚀 INIZIALIZZAZIONE APP
# ========================

app = Flask(__name__)
CORS(app)

bandi_cache = []
ultimo_aggiornamento = None
JSON_FILE = os.path.join(os.path.dirname(__file__), "bandi_database_reale.json")

# ========================
# 🧠 FUNZIONI DI UTILITÀ
# ========================

def carica_bandi_da_json():
    """Carica i bandi dal file locale"""
    global bandi_cache, ultimo_aggiornamento
    try:
        if not os.path.exists(JSON_FILE):
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            bandi_cache = json.load(f)

        ultimo_aggiornamento = datetime.fromtimestamp(os.path.getmtime(JSON_FILE))
        print(f"✅ Caricati {len(bandi_cache)} bandi da {JSON_FILE}")
    except Exception as e:
        print(f"⚠️ Errore caricamento JSON: {e}")
        bandi_cache = []

def aggiorna_bandi_in_background():
    """Esegue genera_database_bandi.py senza bloccare Flask"""
    try:
        print("\n⚙️ Avvio aggiornamento bandi in background...\n")
        result = subprocess.run(
            ["python", "genera_database_bandi.py"],
            capture_output=True,
            text=True,
            timeout=900  # max 15 minuti
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✅ Aggiornamento bandi completato, ricarico il file JSON...")
            carica_bandi_da_json()
        else:
            print(f"⚠️ Errore durante genera_database_bandi.py: {result.stderr}")
    except Exception as e:
        print(f"❌ Errore in aggiornamento bandi: {e}")

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
        "ultimo_aggiornamento": ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None
    })

@app.route("/sitemap.xml")
def serve_sitemap():
    return send_from_directory(os.getcwd(), "sitemap.xml")

@app.route("/robots.txt")
def serve_robots():
    return send_from_directory(os.getcwd(), "robots.txt")

@app.route("/ads.txt")
def serve_ads():
    return send_from_directory(os.getcwd(), "ads.txt")

@app.route("/<path:path>")
def serve_static_files(path):
    """Serve tutti i file statici (index, ads, sitemap, ecc.)"""
    return send_from_directory(".", path)

# ========================
# ⚙️ AVVIO FLASK SU RAILWAY
# ========================

if __name__ == "__main__":
    carica_bandi_da_json()
    # Avvia lo scraping in un thread parallelo
    threading.Thread(target=aggiorna_bandi_in_background, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Server Flask in esecuzione su porta {port}")
    app.run(host="0.0.0.0", port=port)
