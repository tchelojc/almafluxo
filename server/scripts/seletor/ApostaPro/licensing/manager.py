# licensing_manager.py
import sqlite3
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import requests
import json

class LicenseManager:
    def __init__(self, server_url=None, db_conn=None):
        self.conn = db_conn or sqlite3.connect('licenses.db')
        self.SERVER_URL = server_url or "http://localhost:5000"
        self.device_id = self._get_device_id()
        
    def _get_device_id(self) -> str:
        """Gera um ID único para o dispositivo"""
        import uuid
        return str(uuid.getnode())
        
    def verify(self, license_key: str, device_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Verificação simplificada para uso na interface"""
        return self._validate_license(license_key, device_info or {'device_id': self.device_id})
        
    def _validate_license(self, license_key: str, device_info: Dict) -> Dict[str, Any]:
        """Validação completa da licença"""
        # 1. Verificação local
        local_check = self._local_validation(license_key, device_info)
        if not local_check['valid']:
            return local_check
            
        # 2. Verificação no servidor
        try:
            server_check = self._server_validation(license_key, device_info)
            return server_check
        except Exception as e:
            # Fallback para verificação local se o servidor estiver indisponível
            return {
                **local_check,
                'warning': 'server_unavailable',
                'server_message': str(e)
            }
            
    def _local_validation(self, license_key: str, device_info: Dict) -> Dict[str, Any]:
        """Verificação local da licença"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT status, expiration_date, device_id, is_temporary
                FROM licenses 
                WHERE key = ? AND (expiration_date IS NULL OR expiration_date > ?)
            """, (license_key, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            if not result:
                return {
                    'valid': False,
                    'error': 'not_found',
                    'message': 'Licença não encontrada ou expirada'
                }
                
            status, expiration, saved_device_id, is_temp = result
            
            # Verificação de dispositivo
            if saved_device_id and device_info.get('device_id') != saved_device_id:
                return {
                    'valid': False,
                    'error': 'device_mismatch',
                    'message': 'Licença vinculada a outro dispositivo'
                }
                
            return {
                'valid': True,
                'status': status,
                'expiration': expiration,
                'is_temporary': bool(is_temp)
            }
        except sqlite3.Error as e:
            return {
                'valid': False,
                'error': 'database_error',
                'message': f'Erro no banco de dados: {str(e)}'
            }
            
    def _server_validation(self, license_key: str, device_info: Dict) -> Dict[str, Any]:
        """Validação com o servidor remoto"""
        payload = {
            'license_key': license_key,
            'device_id': device_info.get('device_id'),
            'local_time': datetime.now().isoformat(),
            'ip_address': device_info.get('ip_address'),
            'signature': self._generate_signature(license_key, device_info)
        }
        
        response = requests.post(
            f"{self.SERVER_URL}/api/v2/validate",
            json=payload,
            timeout=5
        )
        
        if response.status_code != 200:
            raise Exception(f"Servidor retornou status {response.status_code}")
            
        return response.json()
        
    def _generate_signature(self, license_key: str, device_info: Dict) -> str:
        """Gera assinatura de segurança"""
        message = f"{license_key}{device_info.get('device_id')}{datetime.now().isoformat()}"
        return hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            'sha256'
        ).hexdigest()
        
    def show_activation_ui(self):
        import streamlit as st
        st.error("Licença necessária para continuar")
        license_key = st.text_input("Digite sua chave de licença:")

        if st.button("Ativar"):
            if not license_key:
                st.warning("Por favor, insira uma chave de licença.")
                return

            result = self.verify(license_key)
            if result['valid']:
                st.success("Licença ativada com sucesso!")
                st.session_state.license_valid = True
                st.rerun()
            else:
                st.error(f"Erro: {result.get('message')}")
                
    def soft_verify(self) -> bool:
        """Verificação rápida sem consulta ao servidor"""
        try:
            # Verifica apenas se há uma licença válida na sessão
            return st.session_state.get('license_valid', False)
        except:
            return False
            
    def _clear_session(self):
        """Limpa dados sensíveis da sessão"""
        if 'license_valid' in st.session_state:
            del st.session_state['license_valid']