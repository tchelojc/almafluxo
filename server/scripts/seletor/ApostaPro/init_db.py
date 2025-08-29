import sqlite3
import os
from datetime import datetime

def init_database():
    db_path = os.path.join(os.get.dirname(__file__), 'licenses.db')
    print(f"Inicializando banco em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            email TEXT,
            status TEXT,
            device_id TEXT,
            activation_date TEXT,
            expiration_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
            is_temporary INTEGER DEFAULT 0
        )
    """)
    
    # Insere licença de teste
    cursor.execute("""
        INSERT OR IGNORE INTO licenses (key, status, expiration_date)
        VALUES (?, ?, ?)
    """, (
        "PRO-AA53693D",
        "disponivel",
        "2025-12-31"
    ))
    
    conn.commit()
    conn.close()
    print("✅ Banco inicializado com sucesso")

if __name__ == "__main__":
    init_database()