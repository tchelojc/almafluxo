import sqlite3
from datetime import datetime, timedelta
from auth.hardware import get_hardware_id


class AuthSystem:
    def __init__(self):
        self.hardware_id = get_hardware_id()
        self.db_file = "users.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trials (
                    hardware_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    used INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocked_hardware (
                    hardware_id TEXT PRIMARY KEY
                )
            """)

    def is_blocked(self):
        """Verifica se o hardware está bloqueado"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM blocked_hardware WHERE hardware_id = ?
            """, (self.hardware_id,))
            return cursor.fetchone() is not None

    def activate_trial(self, email: str, trial_days: int = 1):
        """Ativa trial para um email específico"""
        if self.is_blocked():
            raise PermissionError("🚫 Hardware bloqueado para trials.")

        if self.check_trial():
            raise ValueError("⚠️ Trial já ativo nesse dispositivo.")

        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO trials 
                (hardware_id, email, start_time, end_time, used) 
                VALUES (?, ?, datetime('now'), datetime('now', ?), 1)
            """, (self.hardware_id, email, f'+{trial_days} days'))

    def check_trial(self):
        """Verifica se há trial ativo"""
        if self.is_blocked():
            return False

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("""
                    SELECT end_time, used 
                    FROM trials 
                    WHERE hardware_id = ? 
                    ORDER BY end_time DESC 
                    LIMIT 1
                """, (self.hardware_id,))
                trial_data = cursor.fetchone()

                if not trial_data:
                    return False

                end_time, used = trial_data
                if used == 0:
                    return False

                if datetime.fromisoformat(end_time) < datetime.now():
                    return False

                return True

        except Exception as e:
            print(f"Erro ao verificar trial: {str(e)}")
            return False
        
    def check_trial_server(self):
        try:
            response = requests.post(
                f"{self.base_url}/api/check_trial",
                json={
                    "device_id": self.hardware_id
                },
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('active', False)
            else:
                return False
        except:
            return False

    def detect_fraud(self):
        """Detecta tentativa de múltiplos trials"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM trials 
                    WHERE hardware_id = ?
                """, (self.hardware_id,))
                count = cursor.fetchone()[0]

                if count > 2:  # Limite de trials aceitável
                    self._block_hardware()
                    return True
            return False

        except Exception as e:
            print(f"Erro ao detectar fraude: {e}")
            return False

    def _block_hardware(self):
        """Bloqueia o hardware permanentemente"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO blocked_hardware (hardware_id) 
                    VALUES (?)
                """, (self.hardware_id,))
            print("🚫 Hardware bloqueado por tentativa de fraude.")
        except Exception as e:
            print(f"Erro ao bloquear hardware: {e}")
