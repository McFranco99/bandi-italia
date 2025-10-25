# API Server Flask per Bandi Italia - CON 4 SCRAPER INTEGRATI
# Funziona senza PostgreSQL - salva tutto in memoria e JSON
# Scraper inclusi: InPA, Gazzetta Ufficiale, MIMIT, Invitalia

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time
import sys

# Import degli scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Scraper InPA
try:
    from inpa_scraper import InPAScraper
    INPA_AVAILABLE = True
except:
    INPA_AVAILABLE = False
    print("⚠️ InPAScraper non disponibile")

# Scraper Gazzetta Ufficiale
try:
    from gazzetta_scraper import GazzettaScraper
    GAZZETTA_AVAILABLE = True
except:
    GAZZETTA_AVAILABLE = False
    print("⚠️ GazzettaScraper non disponibile")

# Scraper MIMIT
try:
    from mimit_scraper import MIMITScraper
    MIMIT_AVAILABLE = True
except:
    MIMIT_AVAILABLE = False
    print("⚠️ MIMITScraper non disponibile")

# Scraper Invitalia
try:
    from invitalia_scraper import InvitaliaScraper
    INVITALIA_AVAILABLE = True
except:
    INVITALIA_AVAILABLE = False
    print("⚠️ InvitaliaScraper non disponibile")

app = Flask(__name__)
CORS(app)

# Cache dei bandi in memoria
bandi_cache = []
ultimo_aggiornamento = None
JSON_FILE = 'bandi_database_reale.json'



def carica_bandi_da_json():
    global bandi_cache
    print("=== [DEBUG] Avvio caricamento JSON Bandi ===")
    print(f"=== [DEBUG] Cerco file: {JSON_FILE}, esiste? {os.path.exists(JSON_FILE)} ===")
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                bandi_cache = json.load(f)
                print(f"✅ Caricati {len(bandi_cache)} bandi da {JSON_FILE}")
                if len(bandi_cache) > 0:
                    print(f"✪ [DEBUG] Primo bando: {bandi_cache[0]}")
                return True
        else:
            print(f"⚠️ [DEBUG] File {JSON_FILE} non trovato nella cartella: {os.getcwd()}")
    except Exception as e:
        print(f"⚠️ Errore caricamento JSON: {e}")
    return False



def salva_bandi_su_json():
    """Salva bandi su file JSON"""
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(bandi_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvati {len(bandi_cache)} bandi su {JSON_FILE}")
    except Exception as e:
        print(f"⚠️ Errore salvataggio JSON: {e}")

def aggiungi_bando(nuovo_bando):
    """Aggiungi bando evitando duplicati"""
    global bandi_cache
    
    # Controlla se esiste già (per URL)
    for bando in bandi_cache:
        if bando.get('url') == nuovo_bando.get('url'):
            return False
    
    bandi_cache.append(nuovo_bando)
    return True

def aggiorna_bandi_background():
    """Funzione che aggiorna i bandi in background ogni 30 minuti"""
    global bandi_cache, ultimo_aggiornamento
    
    while True:
        try:
            print(f"\n{'='*70}")
            print(f"🔄 Avvio scraping automatico - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            
            nuovi_bandi = 0
            
            # 1. Scrape InPA
            if INPA_AVAILABLE:
                try:
                    print("📡 Scraping InPA...")
                    scraper = InPAScraper()
                    inpa_bandi = scraper.scrape_bandi_list(max_pages=3)
                    
                    for bando in inpa_bandi:
                        if aggiungi_bando(bando):
                            nuovi_bandi += 1
                    
                    print(f"✅ InPA: {len(inpa_bandi)} bandi trovati, {nuovi_bandi} nuovi")
                except Exception as e:
                    print(f"⚠️ Errore scraping InPA: {e}")
            
            # 2. Scrape Gazzetta Ufficiale
            if GAZZETTA_AVAILABLE:
                try:
                    print("📡 Scraping Gazzetta Ufficiale...")
                    scraper = GazzettaScraper()
                    gazzetta_bandi = scraper.scrape_ultimi_30_giorni()
                    
                    count_before = nuovi_bandi
                    for bando in gazzetta_bandi:
                        if aggiungi_bando(bando):
                            nuovi_bandi += 1
                    
                    print(f"✅ Gazzetta: {len(gazzetta_bandi)} bandi trovati, {nuovi_bandi - count_before} nuovi")
                except Exception as e:
                    print(f"⚠️ Errore scraping Gazzetta: {e}")
            
            # 3. Scrape MIMIT
            if MIMIT_AVAILABLE:
                try:
                    print("📡 Scraping MIMIT...")
                    scraper = MIMITScraper()
                    mimit_bandi = scraper.scrape_incentivi()
                    
                    count_before = nuovi_bandi
                    for bando in mimit_bandi:
                        if aggiungi_bando(bando):
                            nuovi_bandi += 1
                    
                    print(f"✅ MIMIT: {len(mimit_bandi)} bandi trovati, {nuovi_bandi - count_before} nuovi")
                except Exception as e:
                    print(f"⚠️ Errore scraping MIMIT: {e}")
            
            # 4. Scrape Invitalia
            if INVITALIA_AVAILABLE:
                try:
                    print("📡 Scraping Invitalia...")
                    scraper = InvitaliaScraper()
                    invitalia_bandi = scraper.scrape_incentivi()
                    
                    count_before = nuovi_bandi
                    for bando in invitalia_bandi:
                        if aggiungi_bando(bando):
                            nuovi_bandi += 1
                    
                    print(f"✅ Invitalia: {len(invitalia_bandi)} bandi trovati, {nuovi_bandi - count_before} nuovi")
                except Exception as e:
                    print(f"⚠️ Errore scraping Invitalia: {e}")
            
            # Salva su JSON
            salva_bandi_su_json()
            
            ultimo_aggiornamento = datetime.now()
            
            print(f"\n{'='*70}")
            print(f"✅ Scraping completato: {len(bandi_cache)} bandi totali")
            print(f"🆕 {nuovi_bandi} nuovi bandi aggiunti in questo ciclo")
            print(f"⏰ Prossimo aggiornamento tra 30 minuti")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"❌ Errore generale scraping: {str(e)}")
        
        # Aspetta 30 minuti prima del prossimo aggiornamento
        time.sleep(30 * 60)

def avvia_scraping_iniziale():
    """Esegui scraping iniziale all'avvio"""
    global ultimo_aggiornamento
    
    print("📡 Carico bandi esistenti da JSON...")
    if carica_bandi_da_json():
        ultimo_aggiornamento = datetime.now()
        print(f"✅ Bandi caricati: {len(bandi_cache)}")
    else:
        print("⚠️ Nessun file JSON trovato, eseguo scraping iniziale...")
        
        # Esegui primo scraping da tutte le fonti disponibili
        nuovi = 0
        
        if INPA_AVAILABLE:
            try:
                scraper = InPAScraper()
                for bando in scraper.scrape_bandi_list(max_pages=3):
                    if aggiungi_bando(bando):
                        nuovi += 1
            except Exception as e:
                print(f"⚠️ Errore InPA: {e}")
        
        if GAZZETTA_AVAILABLE:
            try:
                scraper = GazzettaScraper()
                for bando in scraper.scrape_ultimi_30_giorni():
                    if aggiungi_bando(bando):
                        nuovi += 1
            except Exception as e:
                print(f"⚠️ Errore Gazzetta: {e}")
        
        if MIMIT_AVAILABLE:
            try:
                scraper = MIMITScraper()
                for bando in scraper.scrape_incentivi():
                    if aggiungi_bando(bando):
                        nuovi += 1
            except Exception as e:
                print(f"⚠️ Errore MIMIT: {e}")
        
        if INVITALIA_AVAILABLE:
            try:
                scraper = InvitaliaScraper()
                for bando in scraper.scrape_incentivi():
                    if aggiungi_bando(bando):
                        nuovi += 1
            except Exception as e:
                print(f"⚠️ Errore Invitalia: {e}")
        
        salva_bandi_su_json()
        ultimo_aggiornamento = datetime.now()
        print(f"✅ Primo scraping completato: {len(bandi_cache)} bandi, {nuovi} nuovi")

def avvia_thread_scraping():
    """Avvia thread background per scraping automatico"""
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()

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
        'message': 'Scraping avviato in background'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'bandi_count': len(bandi_cache),
        'ultimo_aggiornamento': ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        'scrapers_disponibili': {
            'inpa': INPA_AVAILABLE,
            'gazzetta': GAZZETTA_AVAILABLE,
            'mimit': MIMIT_AVAILABLE,
            'invitalia': INVITALIA_AVAILABLE
        }
    })
    
@app.route('/api/debug/bandi_json', methods=['GET'])
def debug_bandi_json():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            bandi = json.load(f)
        return jsonify({'success': True, 'count': len(bandi), 'example': bandi[:2]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("=== BOOT FLASK! Inizio log Python visibili ===")
    print("\n" + "="*70)
    print("🚀 API SERVER BANDI ITALIA - 4 SCRAPER INTEGRATI")
    print("="*70)
    print("📌 Salvataggio: File JSON (bandi_database_reale.json)")
    print("📌 Porta: 5000")
    print("📌 CORS: Abilitato")
    print("="*70)
    print("📡 Scraper disponibili:")
    print(f"   • InPA: {'✅' if INPA_AVAILABLE else '❌'}")
    print(f"   • Gazzetta Ufficiale: {'✅' if GAZZETTA_AVAILABLE else '❌'}")
    print(f"   • MIMIT: {'✅' if MIMIT_AVAILABLE else '❌'}")
    print(f"   • Invitalia: {'✅' if INVITALIA_AVAILABLE else '❌'}")
    print("="*70 + "\n")
    
    # Esegui setup iniziale
    avvia_scraping_iniziale()
    
    # Avvia thread scraping automatico
    #avvia_thread_scraping()
    
    print("\n" + "="*70)
    print("✅ SERVER PRONTO!")
    print("="*70)
    print("🌐 API disponibile su: http://localhost:5000/api/bandi")
    print("🏠 Frontend disponibile su: http://localhost:5000/")
    print("📊 Statistiche: http://localhost:5000/api/stats")
    print("🔧 Health check: http://localhost:5000/api/health")
    print("="*70 + "\n")
    
    # Avvia server Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

