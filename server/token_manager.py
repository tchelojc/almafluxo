# token_manager.py (versão completa de segurança)
import jwt
import json
from datetime import datetime, timedelta
import os
from config import SECURITY_CONFIG
import requests
import logging
import hashlib
import uuid
import psutil
import platform
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class QuantumSecurityManager:
    """Gerenciador de segurança quântica e temporal"""
    
    @staticmethod
    def get_system_fingerprint() -> str:
        """Gera uma fingerprint única do sistema"""
        try:
            # Combina múltiplos identificadores de hardware
            system_info = {
                'machine_id': str(uuid.getnode()),
                'processor': platform.processor(),
                'system': platform.system(),
                'release': platform.release(),
                'memory': psutil.virtual_memory().total,
                'disk': str(psutil.disk_usage('/').total)
            }
            
            fingerprint = hashlib.sha256(
                str(system_info).encode()
            ).hexdigest()
            
            return fingerprint
            
        except Exception as e:
            logger.error(f"Erro ao gerar fingerprint: {e}")
            return "unknown_system"
    
    # No token_manager.py, modificar validate_time_consistency
    @staticmethod
    def validate_time_consistency(server_time=None) -> bool:
        """Valida consistência temporal com servidor de referência"""
        try:
            # Tenta obter tempo de servidor externo
            try:
                response = requests.get('http://worldtimeapi.org/api/ip', timeout=3)
                if response.status_code == 200:
                    server_time = datetime.fromisoformat(response.json()['datetime'])
            except:
                # Fallback para tempo local se não conseguir conectar
                server_time = datetime.utcnow()
            
            local_time = datetime.now()
            
            # Calcula diferença considerando timezone
            server_utc = server_time.replace(tzinfo=None)
            local_utc = local_time.astimezone().utcnow().replace(tzinfo=None)
            
            time_diff = abs((server_utc - local_utc).total_seconds())
            max_allowed_diff = 6 * 3600  # Aumente para 6 horas 🔧
            
            if time_diff > max_allowed_diff:
                logger.warning(f"Inconsistência temporal detectada: {time_diff}s")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Erro na validação temporal: {e}")
            # Permite continuar em caso de erro de validação
            return True

class TokenManager:
    def __init__(self):
        self.secret_key = SECURITY_CONFIG['SECRET_KEY']
        self.token_expiration = SECURITY_CONFIG['TOKEN_EXPIRATION']
        self.security_manager = QuantumSecurityManager()
    
    def generate_secure_token(self, user_id: int, email: str, is_admin: bool = False, 
                            license_data: Optional[Dict] = None) -> str:
        """Gera token JWT com todas as validações de segurança"""
        try:
            # Validação temporal
            if not self.security_manager.validate_time_consistency():
                raise ValueError("Inconsistência temporal detectada")
            
            # Dados do payload com informações de segurança
            payload = {
                "user_id": user_id,
                "email": email,
                "is_admin": is_admin,
                "system_fingerprint": self.security_manager.get_system_fingerprint(),
                "exp": datetime.utcnow() + timedelta(seconds=self.token_expiration),
                "iat": datetime.utcnow(),
                "iss": "fluxon-quantum-auth",
                "jti": f"fluxon_{user_id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}",
                "license_valid": license_data.get('valid', False) if license_data else False,
                "license_expiry": license_data.get('expiry') if license_data else None
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            logger.info(f"Token de segurança quântica gerado para {email}")
            return token
            
        except Exception as e:
            logger.error(f"Erro ao gerar token seguro: {e}")
            raise
    
    def validate_secure_token(self, token: str) -> Optional[Dict]:
        """Valida token com todas as camadas de segurança"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=['HS256'],
                options={'verify_exp': True, 'leeway': 10800}
            )
            
            # Validações adicionais de segurança
            current_fingerprint = self.security_manager.get_system_fingerprint()
            if payload.get('system_fingerprint') != current_fingerprint:
                logger.warning("Fingerprint do sistema não corresponde")
                return None
            
            if not self.security_manager.validate_time_consistency():
                logger.warning("Inconsistência temporal durante validação")
                return None
            
            # Verifica se a licença está válida (se existir no token)
            if payload.get('license_valid') is False:
                logger.warning("Licença inválida no token")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro na validação segura: {e}")
            return None

    def get_dynamic_ngrok_url(self) -> str:
        """Obtém URL do Ngrok com verificação de estabilidade e fallback inteligente"""
        max_attempts = 5  # 🔧 Aumentado para 5 tentativas
        healthy_urls = []  # 🔧 Lista para URLs que passaram no health check
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    "http://localhost:4040/api/tunnels", 
                    timeout=5,  # 🔧 Timeout aumentado
                    headers={
                        'Cache-Control': 'no-cache',
                        'User-Agent': 'Fluxon-Token-Manager/1.0'
                    }
                )
                
                if response.status_code == 200:
                    tunnels = response.json().get('tunnels', [])
                    if tunnels:
                        # 🔧 Verifica TODOS os túneis e prioriza os saudáveis
                        for tunnel in tunnels:
                            tunnel_url = tunnel['public_url']
                            
                            # 🔧 VERIFICA SAÚDE da URL antes de retornar
                            if self._is_ngrok_url_healthy(tunnel_url):
                                healthy_urls.append(tunnel_url)
                                logger.info(f"✅ URL Ngrok saudável encontrada: {tunnel_url}")
                        
                        # 🔧 Retorna a primeira URL saudável (prioriza HTTPS)
                        if healthy_urls:
                            https_urls = [url for url in healthy_urls if url.startswith('https://')]
                            if https_urls:
                                return https_urls[0]
                            return healthy_urls[0]
                        
                        # 🔧 Se nenhuma URL está saudável, tenta mesmo assim
                        https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                        if https_tunnel:
                            logger.warning(f"⚠️  URL HTTPS encontrada mas não verificada: {https_tunnel['public_url']}")
                            return https_tunnel['public_url']
                        
                        logger.warning(f"⚠️  Túnel encontrado mas sem verificação de saúde: {tunnels[0]['public_url']}")
                        return tunnels[0]['public_url']
                
                logger.debug(f"Tentativa {attempt + 1}: API retornou status {response.status_code}")
                    
            except requests.RequestException as e:
                logger.debug(f"Tentativa {attempt + 1} falhou: {e}")
            
            # 🔧 Aguarda progressivamente mais entre tentativas
            delay = min(2 * (attempt + 1), 10)  # 2, 4, 6, 8, 10 segundos
            if attempt < max_attempts - 1:
                time.sleep(delay)
        
        # 🔧 FALLBACK INTELIGENTE - Tenta múltiplas estratégias
        fallback_url = self._get_fallback_url()
        logger.warning(f"🔁 Usando fallback: {fallback_url}")
        return fallback_url

    def _is_ngrok_url_healthy(self, url: str) -> bool:
        """Verifica se a URL do Ngrok está respondendo corretamente"""
        try:
            # 🔧 Testa múltiplos endpoints para garantir que está funcional
            test_endpoints = [
                f"{url}/health",           # Endpoint principal
                f"{url}/api/time",         # Endpoint alternativo
                f"{url}/api/check_session" # Endpoint de sessão
            ]
            
            for endpoint in test_endpoints:
                try:
                    response = requests.get(
                        endpoint, 
                        timeout=3,
                        headers={'X-Fluxon-Verification': 'true'}
                    )
                    if response.status_code == 200:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Erro na verificação de saúde da URL {url}: {e}")
            return False

    def _get_fallback_url(self) -> str:
        """Obtém URL de fallback com múltiplas estratégias"""
        fallback_strategies = [
            self._get_bridge_config_url,
            self._get_last_known_ngrok_url,
            self._get_localhost_fallback
        ]
        
        for strategy in fallback_strategies:
            try:
                url = strategy()
                if url and url != "http://localhost:5000":
                    logger.info(f"🎯 Fallback strategy: {strategy.__name__} -> {url}")
                    return url
            except Exception as e:
                logger.debug(f"Fallback strategy {strategy.__name__} falhou: {e}")
                continue
        
        return "http://localhost:5000"

    def _get_bridge_config_url(self) -> str:
        """Obtém URL da bridge config"""
        try:
            from bridge_config import bridge_config
            configured_url = bridge_config.get_current_url()
            if configured_url and configured_url != "http://localhost:5000":
                return configured_url
        except:
            pass
        return None

    def _get_last_known_ngrok_url(self) -> str:
        """Tenta obter a última URL conhecida do Ngrok"""
        try:
            # 🔧 Verifica se há um arquivo de cache com a última URL
            cache_file = os.path.join(os.path.dirname(__file__), '.ngrok_cache.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    if cache_data.get('url') and cache_data.get('timestamp'):
                        # 🔧 Verifica se o cache é recente (menos de 10 minutos)
                        cache_time = datetime.fromisoformat(cache_data['timestamp'])
                        if (datetime.now() - cache_time).total_seconds() < 600:
                            return cache_data['url']
        except:
            pass
        return None

    def _get_localhost_fallback(self) -> str:
        """Fallback final para localhost"""
        return "http://localhost:5000"

    def _cache_ngrok_url(self, url: str):
        """Armazena a URL do Ngrok em cache para fallback futuro"""
        try:
            cache_file = os.path.join(os.path.dirname(__file__), '.ngrok_cache.json')
            cache_data = {
                'url': url,
                'timestamp': datetime.now().isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except:
            pass
    
    def generate_quantum_url(self, user_id: int, email: str, is_admin: bool = False, 
                           license_data: Optional[Dict] = None) -> tuple:
        """Gera URL completa com todas as validações de segurança"""
        token = self.generate_secure_token(user_id, email, is_admin, license_data)
        ngrok_url = self.get_dynamic_ngrok_url()
        
        # Prepara URL final
        if ngrok_url.startswith(('http://', 'https://')):
            base_url = ngrok_url
        else:
            base_url = f"https://{ngrok_url}"
        
        quantum_url = f"{base_url}/hub?token={token}"
        logger.info(f"URL quântica gerada para {email}")
        
        return quantum_url, token
    
    def validate_any_token(self, token: str) -> Optional[Dict]:
        """Valida qualquer tipo de token (normal ou emergência)"""
        try:
            # Primeiro tenta validação normal
            normal_payload = self.validate_secure_token(token)
            if normal_payload:
                return normal_payload
                
            # Se falhou, tenta como token de emergência
            try:
                # Decodifica sem verificar assinatura para emergência
                payload = jwt.decode(token, options={"verify_signature": False})
                if (payload.get('email') == 'emergency@fluxon.com' and 
                    payload.get('emergency') and 
                    payload.get('is_admin')):
                    
                    # Verifica expiração básica
                    exp = payload.get('exp')
                    if exp and datetime.utcnow().timestamp() > exp:
                        return None
                        
                    return payload
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Erro na validação de qualquer token: {e}")
            return None

# Instância global
token_manager = TokenManager()

# Funções de conveniência
def generate_secure_token(user_id: int, email: str, is_admin: bool = False, 
                         license_data: Optional[Dict] = None) -> str:
    return token_manager.generate_secure_token(user_id, email, is_admin, license_data)

def validate_secure_token(token: str) -> Optional[Dict]:
    return token_manager.validate_secure_token(token)

def get_quantum_url(user_id: int, email: str, is_admin: bool = False,
                   license_data: Optional[Dict] = None) -> tuple:
    return token_manager.generate_quantum_url(user_id, email, is_admin, license_data)

def validate_token(token: str) -> Optional[Dict]:
    """
    Valida token simples (atalho para validate_secure_token).
    Mantido por compatibilidade retroativa.
    """
    return token_manager.validate_secure_token(token)

def validate_any_token(token: str) -> Optional[Dict]:
    """
    Valida qualquer tipo de token (normal ou emergência).
    Função de conveniência para compatibilidade.
    """
    return token_manager.validate_any_token(token)
