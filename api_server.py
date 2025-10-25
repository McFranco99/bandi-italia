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
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(bandi_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvati {len(bandi_cache)} bandi su {JSON_FILE}")
    except Exception as e:
        print(f"⚠️ Errore salvataggio JSON: {e}")


def aggiungi_bando(nuovo_bando):
    global bandi_cache
    for bando in bandi_cache:
        if bando.get('url') == nuovo_bando.get('url'):
            return False
    bandi_cache.append(nuovo_bando)
    return True


def aggiorna_bandi_background():
    global bandi_cache, ultimo_aggiornamento

    while True:
        try:
            print(f"\n{'='*70}")
            print(f"🔄 Avvio scraping automatico - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")

            nuovi_bandi_temp = []

            if INPA_AVAILABLE:
                try:
                    scraper = InPAScraper()
                    inpa_bandi = scraper.scrape_bandi_list(max_pages=3)
                    for b in inpa_bandi:
                        if b not in nuovi_bandi_temp:
                            nuovi_bandi_temp.append(b)
                    print(f"✅ InPA: {len(inpa_bandi)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping InPA: {e}")

            if GAZZETTA_AVAILABLE:
                try:
                    scraper = GazzettaScraper()
                    gazzetta_bandi = scraper.scrape_ultimi_30_giorni()
                    for b in gazzetta_bandi:
                        if b not in nuovi_bandi_temp:
                            nuovi_bandi_temp.append(b)
                    print(f"✅ Gazzetta: {len(gazzetta_bandi)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping Gazzetta: {e}")

            if MIMIT_AVAILABLE:
                try:
                    scraper = MIMITScraper()
                    mimit_bandi = scraper.scrape_incentivi()
                    for b in mimit_bandi:
                        if b not in nuovi_bandi_temp:
                            nuovi_bandi_temp.append(b)
                    print(f"✅ MIMIT: {len(mimit_bandi)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping MIMIT: {e}")

            if INVITALIA_AVAILABLE:
                try:
                    scraper = InvitaliaScraper()
                    invitalia_bandi = scraper.scrape_incentivi()
                    for b in invitalia_bandi:
                        if b not in nuovi_bandi_temp:
                            nuovi_bandi_temp.append(b)
                    print(f"✅ Invitalia: {len(invitalia_bandi)} bandi trovati")
                except Exception as e:
                    print(f"⚠️ Errore scraping Invitalia: {e}")

            if len(nuovi_bandi_temp) > 0:
                bandi_cache.clear()
                bandi_cache.extend(nuovi_bandi_temp)
                salva_bandi_su_json()
                print(f"✅ Cache aggiornata con {len(bandi_cache)} bandi")
                ultimo_aggiornamento = datetime.now()
            else:
                print("⚠️ Nessun bando recuperato, cache non aggiornata")

            print(f"\n{'='*70}")
            print(f"⏰ Prossimo aggiornamento tra 30 minuti")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"❌ Errore generale scraping: {str(e)}")

        time.sleep(30 * 60)


def avvia_scraping_iniziale():
    global ultimo_aggiornamento
    print("📡 Carico bandi esistenti da JSON...")
    if carica_bandi_da_json():
        ultimo_aggiornamento = datetime.now()
        print(f"✅ Bandi caricati: {len(bandi_cache)}")
    else:
        print("⚠️ Nessun file JSON trovato, eseguo scraping iniziale...")
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
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()


# ========== ENDPOINT API ==========

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


@app.route('/api/bandi', methods=['GET'])
def get_bandi():
    print(f"[DEBUG] BandI da restituire: {len(bandi_cache)}")
    return jsonify({
        'success': True,
        'count': len(bandi_cache),
        'ultimo_aggiornamento': ultimo_aggiornamento.isoformat() if ultimo_aggiornamento else None,
        'bandi': bandi_cache
    })


@app.route('/api/bandi/categoria/<categoria>', methods=['GET'])
def get_bandi_by_categoria(categoria):
    filtrati = [b for b in bandi_cache if b.get('category') == categoria]
    return jsonify({
        'success': True,
        'count': len(filtrati),
        'categoria': categoria,
        'bandi': filtrati
    })


@app.route('/api/bandi/regione/<regione>', methods=['GET'])
def get_bandi_by_regione(regione):
    filtrati = [b for b in bandi_cache if b.get('region') == regione or b.get('region') == 'nazionale']
    return jsonify({
        'success': True,
        'count': len(filtrati),
        'regione': regione,
        'bandi': filtrati
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
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
    threading.Thread(target=aggiorna_bandi_background, daemon=True).start()
    return jsonify({
        'success': True,
        'message': 'Scraping avviato in background'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
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


@app.route('/api/debug/bandi_status', methods=['GET'])
def debug_bandi_status():
    try:
        file_exists = os.path.exists(JSON_FILE)
        data_preview = []
        if file_exists:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                bandi = json.load(f)
                data_preview = bandi[:3]
        return jsonify({
            'success': True,
            'file_exists': file_exists,
            'bandi_count': len(data_preview),
            'preview': data_preview
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/debug/scrape/<source>')
def debug_scrape(source):
    try:
        if source == 'gazzetta' and GAZZETTA_AVAILABLE:
            scraper = GazzettaScraper()
            result = scraper.scrape_ultimi_30_giorni()
        elif source == 'mimit' and MIMIT_AVAILABLE:
            scraper = MIMITScraper()
            result = scraper.scrape_incentivi()
        elif source == 'invitalia' and INVITALIA_AVAILABLE:
            scraper = InvitaliaScraper()
            result = scraper.scrape_incentivi()
        else:
            return jsonify({'success': False, 'error': 'Scraper non disponibile'})
        return jsonify({'success': True, 'count': len(result), 'sample': result[:3]})
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
    print("="*70 + "\n")
    
    # Esegui setup iniziale
    avvia_scraping_iniziale()
    
    # Avvia thread scraping automatico
    avvia_thread_scraping()
    
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
