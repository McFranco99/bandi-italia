# API Server Flask per Bandi Italia - CON MasterScraper INTEGRATO
# Funziona senza PostgreSQL - salva tutto in memoria e JSON

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_scraper import MasterScraper

app = Flask(__name__)
CORS(app)

# Cache dei bandi in memoria
bandi_cache = []
ultimo_aggiornamento = None

# Inizializza MasterScraper
master_scraper = MasterScraper()

def aggiorna_bandi_background():
    """Funzione che aggiorna i bandi in background ogni 30 minuti"""
    global bandi_cache, ultimo_aggiornamento
    
    while True:
        try:
            print(f"\n{'='*70}")
            print(f"🔄 Avvio scraping master - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")

            nuovi_bandi = master_scraper.run_all_scrapers()

            # Aggiorna cache dal database di MasterScraper
            bandi_cache = master_scraper.db.load_bandi()
            ultimo_aggiornamento = datetime.now()

            print(f"\n{'='*70}")
            print(f"✅ Scraping master completato: {len(bandi_cache)} bandi totali")
            print(f"🆕 {nuovi_bandi} nuovi bandi aggiunti")
            print(f"⏰ Prossimo aggiornamento tra 30 minuti")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"❌ Errore scraping master: {e}")
        
        time.sleep(30 * 60)

def avvia_scraping_iniziale():
    """Esegui scraping iniziale all'avvio"""
    global ultimo_aggiornamento

    print("📡 Carico bandi dal database di MasterScraper...")
    bandi_cache.clear()
    bandi_cache.extend(master_scraper.db.load_bandi())
    
    if bandi_cache:
        ultimo_aggiornamento = datetime.now()
        print(f"✅ Bandi caricati dal DB: {len(bandi_cache)}")
    else:
        print("⚠️ DB vuoto, eseguo scraping iniziale master...")
        nuovi = master_scraper.run_all_scrapers()
        ultimo_aggiornamento = datetime.now()
        print(f"✅ Primo scraping master completato: {len(bandi_cache)} bandi, {nuovi} nuovi")

# ========== ENDPOINT API ==========

@app.route('/')
def serve_frontend():
    """Serve il file index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/api/bandi', methods=['GET'])
def get_bandi():
    """Endpoint principale per recuperare tutti i bandi"""
    return jsonify({
        'success': True,
        'count': len(bandi_cache),
        'ultimo_aggiornamento': ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        'bandi': bandi_cache
    })

@app.route('/api/bandi/categoria/<categoria>', methods=['GET'])
def get_bandi_by_categoria(categoria):
    """Filtra bandi per categoria"""
    filtrati = [b for b in bandi_cache if b.get('category') == categoria]
    return jsonify({
        'success': True,
        'count': len(filtrati),
        'categoria': categoria,
        'bandi': filtrati
    })

@app.route('/api/bandi/regione/<regione>', methods=['GET'])
def get_bandi_by_regione(regione):
    """Filtra bandi per regione"""
    filtrati = [b for b in bandi_cache if b.get('region') == regione or b.get('region') == 'nazionale']
    return jsonify({
        'success': True,
        'count': len(filtrati),
        'regione': regione,
        'bandi': filtrati
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiche aggregate"""
    oggi = datetime.now().date()
    
    bandi_aperti = 0
    bandi_scadenza = 0
    
    for b in bandi_cache:
        if b.get('deadline'):
            try:
                deadline = datetime.fromisoformat(b['deadline'].replace('Z', '+00:00')).date()
                if deadline > oggi:
                    bandi_aperti += 1
                    if (deadline - oggi).days <= 30:
                        bandi_scadenza += 1
            except:
                pass
    
    return jsonify({
        'success': True,
        'stats': {
            'totale': len(bandi_cache),
            'aperti': bandi_aperti,
            'in_scadenza': bandi_scadenza,
            'ultimo_aggiornamento': ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None
        }
    })

@app.route('/api/scrape/now', methods=['POST', 'GET'])
def force_scrape():
    """Forza scraping immediato"""
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()
    return jsonify({
        'success': True,
        'message': 'Scraping master avviato in background'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'bandi_count': len(bandi_cache),
        'ultimo_aggiornamento': ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        'scrapers_disponibili': {
            'inpa': True,
            'gazzetta': True,
            'mimit': True,
            'invitalia': True
        }
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 API SERVER BANDI ITALIA - MASTER SCRAPER INTEGRATO")
    print("="*70 + "\n")
    
    # Setup iniziale
    avvia_scraping_iniziale()
    avvia_thread_scraping()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def avvia_thread_scraping():
    """Avvia thread background per scraping automatico"""
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()
