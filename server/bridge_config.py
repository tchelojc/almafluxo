# bridge_config.py (VERSÃO UNIFICADA - CLOUDFLARE + QUÂNTICO)
import json
from pathlib import Path
import requests
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
import asyncio
import websockets
import subprocess
import time

logger = logging.getLogger(__name__)

class BridgeConfig:
    def __init__(self):
        # Configurações para Cloudflare
        self.cloudflare_config_file = Path(__file__).parent / ".cloudflare_config.json"
        
        # Configurações para sistema quântico (mantidas do original)
        self.config_path = Path(__file__).parent / "bridge_config.json"
        self.config = self._load_config()
        self._session = requests.Session()
        self._session.timeout = 3
        self.quantum_websocket = None
        self.quantum_connected = False
        self.cloudflare_process = None
        
    def _load_config(self):
        """Carrega configuração com validação rigorosa - SEM NGROK"""
        default_config = {
            "cloudflare_url": "https://almafluxo.uk",
            "local_url": "http://localhost:5000", 
            "streamlit_port": 8501,
            "token_key": "fluxon_auth_token",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "prefer_https": True,
            "quantum_enabled": True,
            "quantum_port": 8765,
            "quantum_timeout": 5000,
            "tunnel_type": "cloudflare",
            "cloudflare_tunnel_name": "fluxon-tunnel"
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Remove ngrok_url se existir no arquivo carregado
                    if 'ngrok_url' in loaded:
                        del loaded['ngrok_url']
                    return self._validate_config({**default_config, **loaded})
        except Exception as e:
            logger.error(f"Config load error: {str(e)}")
        
        return default_config
    
    def _load_cloudflare_config(self):
        """Carrega configuração específica do Cloudflare"""
        if self.cloudflare_config_file.exists():
            try:
                with open(self.cloudflare_config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração Cloudflare: {e}")
        return {"url": "https://almafluxo.uk", "last_updated": None, "type": "cloudflare"}
    
    def start_cloudflare_tunnel(self):
        """Inicia o tunnel do Cloudflare em background - VERSÃO MELHORADA"""
        try:
            logger.info(f"Iniciando Cloudflare Tunnel: {self.config['cloudflare_tunnel_name']}")
            
            # Comando para iniciar o tunnel
            cmd = [
                "cloudflared", 
                "tunnel", 
                "run", 
                self.config['cloudflare_tunnel_name']
            ]
            
            # Inicia em background
            self.cloudflare_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread para monitorar a saída e extrair a URL
            def monitor_output():
                url_detected = False
                start_time = time.time()
                
                while self.cloudflare_process and self.cloudflare_process.poll() is None:
                    try:
                        output = self.cloudflare_process.stdout.readline()
                        if output:
                            logger.info(f"Cloudflare: {output.strip()}")
                            
                            # Tenta extrair URL da saída
                            if not url_detected:
                                url = self._extract_url_from_output(output)
                                if url:
                                    self.update_cloudflare_url(url)
                                    url_detected = True
                                    logger.info(f"✅ URL do Cloudflare detectada: {url}")
                            
                        error = self.cloudflare_process.stderr.readline()
                        if error:
                            logger.error(f"Cloudflare Error: {error.strip()}")
                            
                        # Timeout após 30 segundos
                        if time.time() - start_time > 30 and not url_detected:
                            logger.warning("Timeout ao detectar URL do Cloudflare")
                            break
                            
                        time.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Erro no monitoramento Cloudflare: {e}")
                        break
                
                monitor_thread = threading.Thread(target=monitor_output, daemon=True)
                monitor_thread.start()
                
                logger.info("Cloudflare Tunnel iniciado em background")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao iniciar Cloudflare Tunnel: {e}")
            return False

    def _extract_url_from_output(self, output):
        """Extrai URL da saída do cloudflared - ATUALIZADO"""
        patterns = [
            r'https://[a-zA-Z0-9-]+\.try\.cloudflare\.com',
            r'https://[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\.cloudflare\.com',
            r'https://[a-zA-Z0-9-]+\.almafluxo\.uk'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(0)
        
        return None
    
    def get_cloudflare_url(self):
        """Obtém a URL atual do Cloudflare Tunnel - VERSÃO MELHORADA"""
        try:
            # Método 1: Tenta obter via API do Cloudflared
            try:
                cmd = ["cloudflared", "tunnel", "info", self.config['cloudflare_tunnel_name'], "--json"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    if 'hostname' in info:
                        url = f"https://{info['hostname']}"
                        self.update_cloudflare_url(url)
                        return url
            except:
                pass
            
            # Método 2: Verifica se há um processo cloudflared ativo e tenta obter a URL
            try:
                for proc in psutil.process_iter(['name', 'cmdline']):
                    if proc.info['name'] and 'cloudflared' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'tunnel' in cmdline and 'run' in cmdline:
                            # Se encontrou o processo, tenta obter a URL de forma alternativa
                            time.sleep(3)  # Aguarda o tunnel estabilizar
                            return self._try_detect_cloudflare_url()
            except:
                pass
            
            # Método 3: Fallback para URL padrão baseada no nome do tunnel
            return f"https://{self.config['cloudflare_tunnel_name']}.try.cloudflare.com"
            
        except Exception as e:
            logger.error(f"Erro ao obter URL do Cloudflare: {e}")
            return "https://almafluxo.uk"

    def _try_detect_cloudflare_url(self):
        """Tenta detectar a URL do Cloudflare de forma alternativa"""
        try:
            # Tenta conectar à API local do cloudflared
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('public_url'):
                        return tunnel['public_url']
        except:
            pass
        
        # Se não conseguir, retorna a URL padrão
        return f"https://{self.config['cloudflare_tunnel_name']}.almafluxo.uk"
    
    def refresh_cloudflare_url(self):
        """Atualiza imediatamente a URL detectada do Cloudflare"""
        url = self.get_current_url()
        self.config["cloudflare_url"] = url
        return url
    
    def update_cloudflare_url(self, new_url):
        """Atualiza a URL do Cloudflare com validação rigorosa"""
        try:
            parsed = urlparse(new_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("URL inválida")
                
            if new_url != self.config["cloudflare_url"]:
                self.config["cloudflare_url"] = new_url
                self.config["last_updated"] = datetime.now(timezone.utc).isoformat()
                self.config["tunnel_type"] = "cloudflare"
                self._save_config()
                logger.info(f"URL do Cloudflare atualizada: {new_url}")
                
                # Atualiza também via rede quântica se disponível
                if self.quantum_connected:
                    asyncio.run(self.quantum_update_cloudflare_url(new_url))
                    
        except Exception as e:
            logger.warning(f"Falha ao atualizar URL do Cloudflare: {str(e)}")
    
    async def connect_to_quantum_network(self):
        """Conecta-se à rede quântica (mantido do original)"""
        if not self.config.get("quantum_enabled", True):
            logger.info("ℹ️  Comunicação quântica desativada")
            return False
            
        try:
            self.quantum_websocket = await websockets.connect(
                f"ws://localhost:{self.config['quantum_port']}",
                ping_interval=None,
                timeout=self.config.get("quantum_timeout", 5)
            )
            
            # Realizar handshake quântico
            handshake = {
                'type': 'quantum_handshake',
                'service_id': 'bridge_config',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            await self.quantum_websocket.send(json.dumps(handshake))
            response = await self.quantum_websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'quantum_established':
                self.quantum_connected = True
                logger.info("✅ Conectado à rede quântica")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Falha na conexão quântica: {e}")
            
        return False
    
    async def quantum_update_cloudflare_url(self, new_url):
        """Atualiza URL do Cloudflare via rede quântica"""
        if not self.quantum_connected:
            return False
            
        try:
            message = {
                'type': 'quantum_message',
                'action': 'update_cloudflare_url',
                'new_url': new_url,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'bridge_config'
            }
            
            await self.quantum_websocket.send(json.dumps(message))
            logger.info(f"🌐 URL do Cloudflare atualizada via rede quântica: {new_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na atualização quântica: {e}")
            return False
    
    def _validate_config(self, config):
        """Valida todos os campos da configuração - ATUALIZADO SEM NGROK"""
        # Valida URLs
        for url_field in ['cloudflare_url', 'local_url']:  # ✅ REMOVIDO ngrok_url
            if url_field in config:
                try:
                    result = urlparse(config[url_field])
                    if not all([result.scheme, result.netloc]):
                        raise ValueError(f"Invalid URL format for {url_field}")
                except Exception:
                    if url_field == 'cloudflare_url':
                        config[url_field] = "https://almafluxo.uk"
                    else:
                        config[url_field] = "http://localhost:5000"
        
        # Garante que portas são inteiras
        if 'streamlit_port' in config:
            try:
                config['streamlit_port'] = int(config['streamlit_port'])
            except (ValueError, TypeError):
                config['streamlit_port'] = 8501
                
        return config
    
    def update_cloudflare_url(self, new_url):
        """Atualiza a URL do Cloudflare com validação rigorosa"""
        try:
            parsed = urlparse(new_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("URL inválida")
                
            if new_url != self.config["cloudflare_url"]:
                self.config["cloudflare_url"] = new_url
                self.config["last_updated"] = datetime.now(timezone.utc).isoformat()
                self.config["tunnel_type"] = "cloudflare"
                self._save_config()
                logger.info(f"URL do Cloudflare atualizada: {new_url}")
                
                # Atualiza também via rede quântica se disponível
                if self.quantum_connected:
                    asyncio.run(self.quantum_update_cloudflare_url(new_url))
                    
        except Exception as e:
            logger.warning(f"Falha ao atualizar URL do Cloudflare: {str(e)}")
    
    def _check_url_availability(self, url):
        """Verifica se a URL está respondendo - ATUALIZADO PARA CLOUDFLARE"""
        try:
            # Para URLs do Cloudflare, verifica a saúde do servidor
            if 'cloudflare' in url or 'almafluxo.uk' in url:
                test_url = f"{url}/health"
            else:
                # Para URLs locais, verifica a porta 5000 (Flask)
                test_url = url.replace(':8501', ':5000').replace('/streamlit_hub', '/health')
            
            response = self._session.get(test_url, timeout=5)
            # ✅ Aceita qualquer status code 2xx/3xx/4xx (não apenas 200)
            if response.status_code < 500:
                return True
        except Exception as e:
            logger.debug(f"URL verification failed for {test_url}: {str(e)}")
        return False
    
    def get_current_url(self):
        """Obtém a URL ativa com fallback inteligente - SEM NGROK"""
        # Sempre usa Cloudflare como padrão
        tunnel_type = self.config.get("tunnel_type", "cloudflare")
        
        urls_to_try = [
            (self.config["cloudflare_url"], "Cloudflare"),
            (self.config["local_url"], "Local Flask")
        ]
        
        for url, source in urls_to_try:
            if self._check_url_availability(url):
                logger.info(f"Using {source} URL: {url}")
                return url
        
        logger.warning("All URLs failed, using Cloudflare as fallback")
        return self.config.get("cloudflare_url", "https://almafluxo.uk")
    
    def get_streamlit_url(self):
        """Obtém a URL específica para o Streamlit - SEM NGROK"""
        base_url = self.get_current_url()
        
        # Sempre usa o formato Cloudflare
        return f"{base_url}/proxy/streamlit/"
    
    def get_tunnel_type(self):
        """Retorna o tipo de tunnel ativo"""
        return self.config.get("tunnel_type", "cloudflare")
    
    def _save_config(self):
        """Salva a configuração com tratamento de erro robusto (mantido do original)"""
        try:
            temp_path = self.config_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            temp_path.replace(self.config_path)
            
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
    
    def stop_cloudflare_tunnel(self):
        """Para o tunnel do Cloudflare"""
        if self.cloudflare_process:
            try:
                self.cloudflare_process.terminate()
                self.cloudflare_process.wait(timeout=5)
                logger.info("Cloudflare Tunnel parado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao parar Cloudflare Tunnel: {e}")
            finally:
                self.cloudflare_process = None

# Instância singleton com inicialização segura
try:
    bridge_config = BridgeConfig()
    
    # Inicia automaticamente o tunnel Cloudflare se configurado
    if bridge_config.config.get("tunnel_type") == "cloudflare":
        bridge_config.start_cloudflare_tunnel()
        
except Exception as e:
    logging.critical(f"Failed to initialize BridgeConfig: {str(e)}")
    # Fallback extremo
    bridge_config = type('SimpleConfig', (), {
        'get_current_url': lambda: "https://almafluxo.uk",
        'get_streamlit_url': lambda: "https://almafluxo.uk/proxy/streamlit/",
        'get_tunnel_type': lambda: "cloudflare"
    })()