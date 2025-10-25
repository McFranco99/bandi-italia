# Sistema Autenticazione Backend - Flask
# Gestisce: Login, Registrazione, OAuth Google/Apple, Sessioni

from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps
import json

# OAuth libraries
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# OAuth Configuration
oauth = OAuth(app)

# Google OAuth
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Apple OAuth
apple = oauth.register(
    name='apple',
    client_id=os.environ.get('APPLE_CLIENT_ID'),
    client_secret=os.environ.get('APPLE_CLIENT_SECRET'),
    server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'name email'}
)

# Database simulato (in produzione usa PostgreSQL/MongoDB)
users_db = {}  # {email: {password, name, plan, created_at, ...}}
sessions_db = {}  # {token: {email, expires}}

# File per persistenza
USERS_FILE = 'users_data.json'

def load_users():
    """Carica utenti da file"""
    global users_db
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users_db = json.load(f)
    except:
        users_db = {}

def save_users():
    """Salva utenti su file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_db, f, indent=2)
    except Exception as e:
        print(f"Errore salvataggio utenti: {e}")

# Carica utenti all'avvio
load_users()

def token_required(f):
    """Decorator per proteggere endpoint che richiedono autenticazione"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token mancante'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            current_user = users_db.get(data['email'])
            
            if not current_user:
                return jsonify({'error': 'Utente non trovato'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token scaduto'}), 401
        except:
            return jsonify({'error': 'Token invalido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ========== REGISTRAZIONE ==========

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Registrazione nuovo utente"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({'error': 'Campi mancanti'}), 400
    
    if email in users_db:
        return jsonify({'error': 'Email già registrata'}), 400
    
    # Crea nuovo utente
    users_db[email] = {
        'password': generate_password_hash(password),
        'name': name,
        'plan': 'free',  # free, pro, business
        'created_at': datetime.datetime.now().isoformat(),
        'preferences': {},
        'saved_bandi': []
    }
    
    save_users()
    
    # Genera token
    token = jwt.encode({
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.secret_key, algorithm='HS256')
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'email': email,
            'name': name,
            'plan': 'free'
        }
    }), 201

# ========== LOGIN ==========

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login con email e password"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email e password richiesti'}), 400
    
    user = users_db.get(email)
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Credenziali non valide'}), 401
    
    # Genera token
    token = jwt.encode({
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.secret_key, algorithm='HS256')
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'email': email,
            'name': user['name'],
            'plan': user.get('plan', 'free')
        }
    })

# ========== OAUTH GOOGLE ==========

@app.route('/api/auth/google')
def google_login():
    """Avvia login Google"""
    redirect_uri = 'http://localhost:5000/api/auth/google/callback'
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/google/callback')
def google_callback():
    """Callback Google OAuth"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        # Crea o aggiorna utente
        if email not in users_db:
            users_db[email] = {
                'name': name,
                'plan': 'free',
                'created_at': datetime.datetime.now().isoformat(),
                'oauth_provider': 'google',
                'preferences': {},
                'saved_bandi': []
            }
            save_users()
        
        # Genera token
        jwt_token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, app.secret_key, algorithm='HS256')
        
        # Redirect al frontend con token
        return redirect(f'/?token={jwt_token}')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== OAUTH APPLE ==========

@app.route('/api/auth/apple')
def apple_login():
    """Avvia login Apple"""
    redirect_uri = 'http://localhost:5000/api/auth/apple/callback'
    return apple.authorize_redirect(redirect_uri)

@app.route('/api/auth/apple/callback')
def apple_callback():
    """Callback Apple OAuth"""
    try:
        token = apple.authorize_access_token()
        user_info = token.get('userinfo')
        
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        # Crea o aggiorna utente
        if email not in users_db:
            users_db[email] = {
                'name': name,
                'plan': 'free',
                'created_at': datetime.datetime.now().isoformat(),
                'oauth_provider': 'apple',
                'preferences': {},
                'saved_bandi': []
            }
            save_users()
        
        # Genera token
        jwt_token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, app.secret_key, algorithm='HS256')
        
        return redirect(f'/?token={jwt_token}')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== PROFILO UTENTE ==========

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Ottieni dati profilo utente"""
    return jsonify({
        'success': True,
        'user': {
            'email': current_user.get('email'),
            'name': current_user.get('name'),
            'plan': current_user.get('plan', 'free'),
            'created_at': current_user.get('created_at'),
            'preferences': current_user.get('preferences', {}),
            'saved_bandi': current_user.get('saved_bandi', [])
        }
    })

@app.route('/api/user/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Aggiorna profilo utente"""
    data = request.get_json()
    
    # Aggiorna campi permessi
    if 'name' in data:
        current_user['name'] = data['name']
    if 'preferences' in data:
        current_user['preferences'] = data['preferences']
    
    save_users()
    
    return jsonify({'success': True, 'user': current_user})

# ========== BANDI SALVATI ==========

@app.route('/api/user/saved-bandi', methods=['POST'])
@token_required
def save_bando(current_user):
    """Salva un bando nei preferiti"""
    data = request.get_json()
    bando_id = data.get('bando_id')
    
    if not bando_id:
        return jsonify({'error': 'ID bando mancante'}), 400
    
    if 'saved_bandi' not in current_user:
        current_user['saved_bandi'] = []
    
    if bando_id not in current_user['saved_bandi']:
        current_user['saved_bandi'].append(bando_id)
        save_users()
    
    return jsonify({'success': True})

@app.route('/api/user/saved-bandi/<int:bando_id>', methods=['DELETE'])
@token_required
def remove_saved_bando(current_user, bando_id):
    """Rimuovi un bando dai preferiti"""
    if 'saved_bandi' in current_user and bando_id in current_user['saved_bandi']:
        current_user['saved_bandi'].remove(bando_id)
        save_users()
    
    return jsonify({'success': True})

# ========== LOGOUT ==========

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout utente"""
    # Nel caso di JWT, il logout è gestito lato client eliminando il token
    return jsonify({'success': True})

if __name__ == '__main__':
    print("🔐 Sistema Autenticazione Attivo")
    print("📍 Endpoints disponibili:")
    print("   POST /api/auth/register")
    print("   POST /api/auth/login")
    print("   GET  /api/auth/google")
    print("   GET  /api/auth/apple")
    print("   GET  /api/user/profile")
    print("   PUT  /api/user/profile")
    print("   POST /api/user/saved-bandi")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
