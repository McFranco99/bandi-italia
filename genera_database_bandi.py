import json
import base64
import requests
import os
from datetime import datetime
from inpa_scraper import InPAScraper
from invitalia_scraper import InvitaliaScraper
from mimit_scraper import MIMITScraper
from consap_scraper import ConsapScraper
from gazzetta_scraper import GazzettaScraper


# =========================================================
# 🧠 GENERAZIONE DATABASE BANDI
# =========================================================

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


# =========================================================
# 💾 SALVATAGGIO + UPLOAD SU GITHUB
# =========================================================

def save_to_json():
    bandi = generate_real_bandi_database()
    file_path = 'bandi_database_reale.json'

    # 🔹 Salva in locale
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(bandi, f, ensure_ascii=False)
    print(f"💾 File salvato con {len(bandi)} bandi.")

    # 📊 Log riepilogativo
    try:
        print("\n📊 Riepilogo per sorgente:")
        sorgenti = {}
        for bando in bandi:
            src = bando.get("source", "sconosciuta")
            sorgenti[src] = sorgenti.get(src, 0) + 1
        for src, count in sorgenti.items():
            print(f"   - {src}: {count} bandi")
        print("✅ Aggiornamento completato con successo.\n")
    except Exception as e:
        print(f"⚠️ Errore durante il riepilogo: {e}")

    # 🚀 Push su GitHub via API
    push_to_github(file_path)


# =========================================================
# 🚀 PUSH DIRETTO VIA API GITHUB
# =========================================================

def push_to_github(file_path="bandi_database_reale.json"):
    """Carica il file aggiornato direttamente su GitHub tramite API REST."""
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = "McFranco99/bandi-italia"
        branch = "main"
        commit_message = f"Aggiornamento automatico bandi ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

        if not token:
            print("⚠️ Nessun token GitHub trovato (variabile GITHUB_TOKEN mancante).")
            return

        # Legge il file e lo converte in base64
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        # Recupera lo SHA del file attuale (per aggiornamento)
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None

        # Crea il payload per la PUT
        payload = {
            "message": commit_message,
            "content": content,
            "branch": branch,
            "committer": {
                "name": "BandiperteBot",
                "email": "bot@bandiperte.it"
            }
        }
        if sha:
            payload["sha"] = sha

        r = requests.put(url, headers=headers, json=payload)

        if r.status_code in (200, 201):
            print("✅ File aggiornato su GitHub con successo via API.")
        else:
            print(f"⚠️ Errore API GitHub ({r.status_code}): {r.text}")

    except Exception as e:
        print(f"❌ Errore durante il push su GitHub via API: {e}")


if __name__ == "__main__":
    save_to_json()
