# ---------- NOVO ARQUIVO: connection_manager.py ----------
"""
Sistema avançado de gerenciamento de conexões para o ALMA Platform
Gerencia cache, fallbacks e monitoramento de conexões Ngrok
"""

import json
import time
import requests
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning
import logging

# Suprimir avisos de SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ConnectionManager")

class ConnectionManager:
    """Gerenciador avançado de conexões para o sistema ALMA"""
    
    _instance = None
    _cache = {}
    _last_update = 0
    CACHE_DURATION = 30  # segundos
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance
    
    def _init_manager(self):
        """Inicializa o gerenciador de conexões"""
        self.possible_config_paths = [
            Path(__file__).parent.parent / "server" / ".ngrok_coordinator.json",
            Path(__file__).parent / ".ngrok_redirects.json",
            Path(__file__).parent / ".ngrok_coordinator.json"
        ]
        
        # URLs de fallback pré-definidas
        self.fallback_urls = [
            "https://47aecb2cefb9.ngrok-free.app",
            "http://localhost:5000",
            "http://192.168.99.170:5000"
        ]
        
        logger.info("ConnectionManager inicializado")
    
    def get_current_ngrok_url(self, force_refresh=False):
        """
        Obtém a URL atual do Ngrok com cache inteligente
        """
        current_time = time.time()
        
        # Verifica se o cache é válido
        if not force_refresh and 'ngrok_url' in self._cache:
            if current_time - self._last_update < self.CACHE_DURATION:
                logger.debug("Usando URL em cache")
                return self._cache['ngrok_url']
        
        # Tenta obter a URL do coordenador
        ngrok_url = self._get_url_from_coordinator()
        
        # Fallback para método de detecção automática
        if not ngrok_url:
            ngrok_url = self._detect_ngrok_url()
        
        # Atualiza cache
        if ngrok_url:
            self._cache['ngrok_url'] = ngrok_url
            self._last_update = current_time
            logger.info(f"URL do Ngrok atualizada: {ngrok_url}")
        
        return ngrok_url
    
    def _get_url_from_coordinator(self):
        """Obtém a URL do arquivo de coordenação do Ngrok"""
        for config_path in self.possible_config_paths:
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Suporte a formato multiporta
                    if 'urls' in config and config['urls']:
                        return config['urls'].get('proxy') or next(iter(config['urls'].values()))
                    
                    # Suporte a formato antigo
                    if 'url' in config:
                        return config['url']
                    
                    logger.debug(f"Formato de config não reconhecido em {config_path}")
            except Exception as e:
                logger.warning(f"Erro ao ler {config_path}: {e}")
                continue
        
        return None
    
    def _detect_ngrok_url(self):
        """Tenta detectar a URL do Ngrok automaticamente"""
        # Tenta API local do Ngrok
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3, verify=False)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        return tunnel['public_url']
        except:
            pass
        
        # Testa URLs de fallback
        for url in self.fallback_urls:
            if self._test_connection(url):
                return url
        
        return None
    
    def _test_connection(self, url, timeout=3):
        """Testa se uma URL está respondendo"""
        try:
            health_url = f"{url}/health" if not url.endswith('/health') else url
            response = requests.get(health_url, timeout=timeout, verify=False)
            return response.status_code == 200
        except:
            return False
    
    def get_connection_status(self):
        """Retorna o status atual de todas as conexões"""
        status = {
            'ngrok_url': self.get_current_ngrok_url(),
            'local_available': self._test_connection("http://localhost:5000"),
            'streamlit_available': self._test_connection("http://localhost:8501/_stcore/health"),
            'timestamp': time.time(),
            'cache_age': time.time() - self._last_update if self._last_update else None
        }
        
        return status

# Singleton global
connection_manager = ConnectionManager()