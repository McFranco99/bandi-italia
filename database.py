"""
Database Manager - Gestisce salvataggio e recupero bandi
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bandi_italia'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432)
        )
        self.create_tables()
    
    def create_tables(self):
        """Crea tabelle se non esistono"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bandi (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                category VARCHAR(50) NOT NULL,
                region VARCHAR(100),
                entity VARCHAR(200),
                description TEXT,
                amount INTEGER DEFAULT 0,
                deadline DATE,
                published DATE,
                url TEXT,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, entity, deadline)
            );
            
            CREATE INDEX IF NOT EXISTS idx_bandi_category ON bandi(category);
            CREATE INDEX IF NOT EXISTS idx_bandi_region ON bandi(region);
            CREATE INDEX IF NOT EXISTS idx_bandi_deadline ON bandi(deadline);
        """)
        
        self.conn.commit()
        cursor.close()
    
    def save_bandi(self, bandi_list):
        """Salva lista di bandi in database (skip duplicati)"""
        cursor = self.conn.cursor()
        new_count = 0
        
        for bando in bandi_list:
            try:
                cursor.execute("""
                    INSERT INTO bandi (title, category, region, entity, description, 
                                      amount, deadline, published, url, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, entity, deadline) DO NOTHING
                    RETURNING id;
                """, (
                    bando.get('title'),
                    bando.get('category'),
                    bando.get('region'),
                    bando.get('entity'),
                    bando.get('description'),
                    bando.get('amount', 0),
                    bando.get('deadline'),
                    bando.get('published'),
                    bando.get('url'),
                    bando.get('source')
                ))
                
                if cursor.fetchone():
                    new_count += 1
                    
            except Exception as e:
                print(f"Errore salvataggio bando: {str(e)}")
                self.conn.rollback()
                continue
        
        self.conn.commit()
        cursor.close()
        
        return new_count
    
    def get_all_bandi(self):
        """Recupera tutti i bandi attivi"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, title, category, region, entity, description,
                   amount, deadline, published, url, source
            FROM bandi
            WHERE deadline >= CURRENT_DATE
            ORDER BY published DESC;
        """)
        
        columns = [desc for desc in cursor.description]
        bandi = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        return bandi
    
    def close(self):
        """Chiudi connessione"""
        self.conn.close()
