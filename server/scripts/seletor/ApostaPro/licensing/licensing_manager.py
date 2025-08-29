import sqlite3
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import requests
import json
import uuid
import os

class LicenseManager:
    def __init__(self, server_url=None, db_path='licenses.db'):
        self.SERVER_URL = server_url or "http://localhost:5000"
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        
    def _init_db(self):
        """Inicializa o banco de dados se não existir"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key TEXT PRIMARY KEY,
                status TEXT,
                device_id TEXT,
                expiration_date TEXT,
                is_temporary INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def _get_device_id(self) -> str:
        """Gera um ID único para o dispositivo"""
        return str(uuid.getnode())
        
    def verify(self, license_key: str, strict_check=False) -> Dict[str, Any]:
        """Verificação principal da licença"""
        device_info = {'device_id': self._get_device_id()}
        
        # 1. Verificação local
        local_check = self._local_check(license_key, device_info)
        if not local_check['valid'] and strict_check:
            return local_check
            
        # 2. Verificação no servidor (se necessário)
        if strict_check or not local_check['valid']:
            try:
                server_check = self._server_check(license_key, device_info)
                if server_check['valid']:
                    return server_check
            except Exception as e:
                if strict_check:
                    return {
                        'valid': False,
                        'error': 'server_error',
                        'message': str(e)
                    }
        
        return local_check

    def _local_check(self, license_key: str, device_info: Dict) -> Dict[str, Any]:
        """Verificação local no banco de dados"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT status, device_id, expiration_date 
            FROM licenses 
            WHERE key = ? AND (expiration_date IS NULL OR expiration_date > ?)
        """, (license_key, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        if not result:
            return {'valid': False, 'error': 'license_not_found'}
            
        status, saved_device_id, expiration = result
        
        if saved_device_id and saved_device_id != device_info['device_id']:
            return {'valid': False, 'error': 'device_mismatch'}
            
        return {
            'valid': True,
            'status': status,
            'expiration': expiration
        }

    def _server_check(self, license_key: str, device_info: Dict) -> Dict[str, Any]:
        """Verificação com o servidor remoto"""
        payload = {
            'license_key': license_key,
            'device_id': device_info['device_id'],
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{self.SERVER_URL}/validate",
            json=payload,
            timeout=5
        )
        
        return response.json()