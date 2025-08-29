import time
import requests
import subprocess
import os
import json
import re
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("NgrokCoordinator")

class NgrokCoordinator:
    def __init__(self):
        self.current_pid = None
        self.current_url = None
        self.config_file = Path(__file__).parent / ".ngrok_coordinator.json"
        self.redirect_config = Path(__file__).parent / ".ngrok_redirects.json"  # NOVO: Config de redirecionamento
        self.client_dir = Path(__file__).parent.parent / "client"
        self.history_file = Path(__file__).parent / ".ngrok_history.json"  # NOVO: Histórico de URLs
        self.load_config()
    
    def load_config(self):
        """Carrega configuração persistente - MANTIDO ORIGINAL"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_pid = config.get('pid')
                    self.current_url = config.get('url')
            
            # NOVO: Carregar configuração de redirecionamento
            if self.redirect_config.exists():
                with open(self.redirect_config, 'r') as f:
                    redirect_config = json.load(f)
                    # Mantém compatibilidade com sistemas existentes
            else:
                # Cria arquivo de redirecionamento se não existir
                self.save_redirect_config()
                
            # NOVO: Carregar histórico se existir
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.ngrok_history = json.load(f)
            else:
                self.ngrok_history = {}
                
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            self.current_pid = None
            self.current_url = None
            self.ngrok_history = {}
    
    # ✅ ADICIONE ESTA FUNÇÃO DENTRO DA CLASSE NgrokCoordinator:
    def save_config(self):
        """Salva configuração atual - VERSÃO MELHORADA PARA MULTIPORTAS"""
        try:
            # ✅ OBTÉM TODOS OS TÚNEIS ATIVOS
            all_tunnels = self.get_ngrok_tunnels() or {}
            
            config = {
                'pid': self.current_pid,
                'url': self.current_url,  # ✅ MANTÉM COMPATIBILIDADE
                'urls': all_tunnels,      # ✅ NOVO: TODOS OS TÚNEIS
                'timestamp': time.time(),
                'version': '2.0-multiport'
            }
            
            # ✅ SALVA EM AMBOS OS DIRETÓRIOS
            self.save_config_to_both_locations(config)
                    
            # ✅ ATUALIZA CONFIG DE REDIRECIONAMENTO
            self.save_redirect_config()
            
            # ✅ SALVA NO HISTÓRICO
            self.save_to_history()
            
            logger.info(f"✅ Config salva com {len(all_tunnels)} túneis")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar config: {e}")
    
    def save_redirect_config(self):
        """NOVO: Salva configuração para o servidor de redirecionamento"""
        try:
            config = {'current_ngrok': self.current_url}
            with open(self.redirect_config, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar config de redirecionamento: {e}")
    
    def save_to_history(self):
        """NOVO: Salva URL no histórico"""
        try:
            if self.current_url:
                self.ngrok_history[self.current_url] = {
                    'timestamp': time.time(),
                    'active': True
                }
                with open(self.history_file, 'w') as f:
                    json.dump(self.ngrok_history, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            
    def save_config_to_both_locations(self, config):
        """Salva a configuração tanto no diretório server quanto no client"""
        try:
            # ✅ SALVA NO DIRETÓRIO SERVER (original)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # ✅ SALVA NO DIRETÓRIO CLIENT (para o servidor web)
            client_config_file = self.client_dir / ".ngrok_coordinator.json"
            with open(client_config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"✅ Configuração salva em ambos os diretórios")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar configuração em ambos os locais: {e}")
    
    def is_ngrok_running(self):
        """Verifica se o Ngrok já está rodando - MANTIDO ORIGINAL"""
        try:
            if os.name == 'nt':
                result = subprocess.run(["tasklist", "/fi", "imagename eq ngrok.exe"], 
                                      capture_output=True, text=True)
                return "ngrok.exe" in result.stdout
            else:
                result = subprocess.run(["pgrep", "-f", "ngrok"], 
                                      capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
    
    def get_existing_ngrok_url(self):
        """Tenta obter URL de Ngrok já existente - MANTIDO ORIGINAL"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        return tunnel['public_url']
        except:
            pass
        return None
    
    def update_html_files(self, new_ngrok_url):
        """Atualiza automaticamente todos os arquivos HTML - MANTIDO ORIGINAL"""
        try:
            if not self.client_dir.exists():
                logger.warning(f"Diretório client não encontrado: {self.client_dir}")
                return False
            
            html_files = ['link_alma.html', 'index_external.html', 'index_internal.html']
            updated_count = 0
            
            for file_name in html_files:
                file_path = self.client_dir / file_name
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        
                        # Substitui qualquer URL ngrok antiga pela nova
                        old_pattern = r'https://[a-z0-9-]+\.ngrok-free\.app'
                        new_content = re.sub(old_pattern, new_ngrok_url, content)
                        
                        # Atualiza específicamente o fallback no JavaScript
                        js_patterns = [
                            r"fallbackNgrok: 'https://[a-z0-9-]+\.ngrok-free\.app'",
                            r'fallbackNgrok: "https://[a-z0-9-]+\.ngrok-free\.app"'
                        ]
                        
                        for pattern in js_patterns:
                            new_js = f"fallbackNgrok: '{new_ngrok_url}'"
                            new_content = re.sub(pattern, new_js, new_content)
                        
                        # Atualiza data attributes
                        data_pattern = r'data-ngrok-url="https://[a-z0-9-]+\.ngrok-free\.app'
                        new_data = f'data-ngrok-url="{new_ngrok_url}'
                        new_content = re.sub(data_pattern, new_data, new_content)
                        
                        if new_content != content:
                            with open(file_path, 'w', encoding='utf-8') as file:
                                file.write(new_content)
                            logger.info(f"✅ {file_name} atualizado com: {new_ngrok_url}")
                            updated_count += 1
                        else:
                            logger.debug(f"ℹ️  {file_name} já está atualizado")
                            
                    except Exception as e:
                        logger.error(f"❌ Erro ao atualizar {file_name}: {e}")
                else:
                    logger.debug(f"ℹ️  Arquivo não encontrado: {file_name}")
            
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro geral na atualização HTML: {e}")
            return False
    
    def start_ngrok(self):
        """Inicia Ngrok apenas se não estiver rodando - MANTIDO ORIGINAL"""
        logger.info("🔧 Coordenador Ngrok iniciado")
        
        # Verifica se já está rodando
        if self.is_ngrok_running():
            logger.info("✅ Ngrok já está em execução")
            existing_url = self.get_existing_ngrok_url()
            if existing_url:
                self.current_url = existing_url
                self.save_config()
                logger.info(f"🌐 URL existente: {existing_url}")
                
                # Atualiza HTMLs com URL existente
                self.update_html_files(existing_url)
                
                return existing_url
        
        # Mata processos antigos para garantir limpeza
        self.kill_ngrok()
        time.sleep(2)
        
        # Inicia novo processo
        logger.info("🚀 Iniciando novo túnel Ngrok...")
        try:
            process = subprocess.Popen([
                "ngrok", "http", "5000", 
                "--log=stdout",
                "--log-level=info"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.current_pid = process.pid
            logger.info(f"✅ Ngrok iniciado (PID: {process.pid})")
            
            # Aguarda inicialização
            time.sleep(7)
            
            # Obtém URL
            for _ in range(12):
                url = self.get_existing_ngrok_url()
                if url:
                    self.current_url = url
                    self.save_config()
                    logger.info(f"🌐 Nova URL: {url}")
                    
                    # Atualiza HTMLs automaticamente
                    if self.update_html_files(url):
                        logger.info("🎯 Arquivos HTML atualizados automaticamente")
                    
                    return url
                time.sleep(1)
            
            logger.error("❌ Não foi possível obter URL do Ngrok")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Ngrok: {e}")
            return None
    
    def kill_ngrok(self):
        """Mata todos os processos Ngrok - MANTIDO ORIGINAL"""
        try:
            if os.name == 'nt':
                subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], 
                             capture_output=True, shell=True)
            else:
                subprocess.run(["pkill", "-9", "-f", "ngrok"], 
                             capture_output=True)
            logger.info("✅ Processos Ngrok encerrados")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Erro ao encerrar Ngrok: {e}")

    def check_timezone_compatibility(self):
        """Verifica compatibilidade de timezone - VERSÃO SUPER TOLERANTE"""
        try:
            # ✅ Tenta conectar ao Flask mas NÃO FALHA se não conseguir
            response = requests.get("http://localhost:5000/api/timezone/debug", timeout=2)
            if response.status_code == 200:
                timezone_info = response.json()
                timezone_offset = timezone_info.get('timezone_offset', 0)
                
                if abs(timezone_offset) > 3:
                    print(f"⚠️  AVISO: Diferença de timezone detectada: {timezone_offset:.1f}h")
                    return False
                    
                print(f"🌐 Timezone OK: offset={timezone_offset:.1f}h")
                return True
                
        except requests.exceptions.ConnectionError:
            # ✅ NÃO É ERRO - Flask simplesmente não está rodando ainda
            pass
        except Exception as e:
            # ✅ QUALQUER OUTRO ERRO É IGNORADO
            pass
            
        return True  # ✅ SEMPRE RETORNA True PARA NÃO BLOQUEAR

    def monitor_ngrok_url(self):
        """Monitora continuamente a URL do Ngrok"""
        print("📡 Iniciando monitoramento contínuo multiporta...")
        
        # ✅ VERIFICAÇÃO OPCIONAL - NÃO BLOQUEIA
        try:
            if not self.check_timezone_compatibility():
                print("💡 Dica: Verifique a sincronização de horário do sistema")
        except:
            pass  # ✅ IGNORA QUALQUER ERRO
        
        last_tunnels = {}
        
        while True:
            try:
                # ✅ OBTÉM TODOS OS TÚNEIS
                current_tunnels = self.get_ngrok_tunnels() or {}
                
                if not current_tunnels:
                    logger.warning("⚠️ Nenhum túnel Ngrok detectado")
                    time.sleep(20)
                    continue
                
                # ✅ VERIFICA SAÚDE DE CADA TÚNEL
                healthy_tunnels = {}
                for tunnel_name, tunnel_url in current_tunnels.items():
                    if self.verify_tunnel_health(tunnel_url, tunnel_name):
                        healthy_tunnels[tunnel_name] = tunnel_url
                        logger.debug(f"✅ {tunnel_name}: {tunnel_url}")
                    else:
                        logger.warning(f"⚠️ {tunnel_name} não saudável: {tunnel_url}")
                
                # ✅ ATUALIZA SE HOUVER MUDANÇAS
                if healthy_tunnels != last_tunnels:
                    if healthy_tunnels:
                        logger.info(f"🔄 Mudança detectada: {len(healthy_tunnels)} túneis saudáveis")
                        
                        # ✅ ATUALIZA URL PRINCIPAL (para compatibilidade)
                        self.current_url = healthy_tunnels.get('proxy') or next(iter(healthy_tunnels.values()))
                        
                        # ✅ SALVA CONFIGURAÇÃO COMPLETA
                        self.save_config()
                        
                        # ✅ ATUALIZA HTMLs APENAS SE URL PRINCIPAL MUDOU
                        if self.current_url != (last_tunnels.get('proxy') if last_tunnels else None):
                            if self.update_html_files(self.current_url):
                                logger.info("🎯 Arquivos HTML atualizados")
                        
                        last_tunnels = healthy_tunnels
                    else:
                        logger.warning("💥 Todos os túneis insaudáveis")
                
                time.sleep(25)  # ✅ AUMENTADO PARA 25s
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoramento interrompido")
                break
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento: {e}")
                time.sleep(30)
                
    def sync_with_ngrok_manager(self):
        """Sincroniza com o ngrok_manager.py para consistência"""
        try:
            # ✅ VERIFICA SE O NGROK_MANAGER ESTÁ RODANDO
            manager_config_path = Path(__file__).parent / ".ngrok_coordinator.json"
            if manager_config_path.exists():
                with open(manager_config_path, 'r') as f:
                    manager_config = json.load(f)
                
                # ✅ COMPARA CONFIGURAÇÕES
                current_tunnels = self.get_ngrok_tunnels() or {}
                manager_tunnels = manager_config.get('urls', {})
                
                if current_tunnels != manager_tunnels:
                    logger.info("🔄 Sincronizando com ngrok_manager...")
                    # ✅ ATUALIZA MANAGER COM NOSSOS TÚNEIS
                    self.save_config()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
            return False
                
    def get_ngrok_tunnels(self):
        """Busca todos os túneis ativos da API do Ngrok - VERSÃO MELHORADA"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=8)
            response.raise_for_status()
            tunnels_data = response.json().get('tunnels', [])
            
            urls = {}
            for tunnel in tunnels_data:
                if tunnel.get('proto') == 'https':
                    public_url = tunnel.get('public_url')
                    config_addr = tunnel.get('config', {}).get('addr', '')
                    
                    # ✅ DETECÇÃO INTELIGENTE MELHORADA
                    if ':5000' in config_addr or 'localhost:5000' in config_addr:
                        urls['proxy'] = public_url
                    elif ':8501' in config_addr or 'localhost:8501' in config_addr:
                        urls['streamlit'] = public_url
                    elif ':5500' in config_addr:
                        urls['quantum_proxy'] = public_url
                    elif ':5001' in config_addr:
                        urls['redirect'] = public_url
                    else:
                        # ✅ IDENTIFICA POR NOME DO TÚNEL TAMBÉM
                        tunnel_name = tunnel.get('name', '')
                        if tunnel_name:
                            urls[tunnel_name] = public_url
                        else:
                            urls[f'tunnel_{len(urls)}'] = public_url
            
            return urls
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao acessar API Ngrok: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            return None
    
    def verify_tunnel_health(self, url, tunnel_type='proxy'):
        """Verifica se um túnel está saudável - VERSÃO MELHORADA"""
        if not url:
            return False
        
        # ✅ PATHS ESPECÍFICOS POR TIPO DE TÚNEL
        health_paths = {
            'proxy': ['/health', '/api/status', '/'],
            'streamlit': ['/_stcore/health', '/'],
            'quantum_proxy': ['/health', '/'],
            'redirect': ['/'],
            'default': ['/health', '/', '/api/status']
        }
        
        paths_to_test = health_paths.get(tunnel_type, health_paths['default'])
        
        for path in paths_to_test:
            try:
                test_url = f"{url.rstrip('/')}{path}"
                response = requests.get(
                    test_url,
                    headers={
                        'X-Fluxon-Verification': 'true',
                        'User-Agent': 'NgrokCoordinator/2.0',
                        'ngrok-skip-browser-warning': 'true'
                    },
                    timeout=10,
                    allow_redirects=True
                )
                
                # ✅ ACEITA QUALQUER RESPOSTA VÁLIDA (2xx, 3xx, 4xx)
                if response.status_code < 500:
                    logger.debug(f"✅ {tunnel_type} saudável: {test_url} ({response.status_code})")
                    return True
                    
            except requests.exceptions.Timeout:
                logger.debug(f"⏰ Timeout em {test_url}")
                continue
            except requests.exceptions.ConnectionError:
                logger.debug(f"🔌 Connection error em {test_url}")
                continue
            except Exception as e:
                logger.debug(f"❌ Erro em {test_url}: {e}")
                continue
        
        # ✅ FALLBACK: Verificação TCP
        try:
            import socket
            from urllib.parse import urlparse
            
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                logger.debug(f"✅ {tunnel_type} respondendo na porta {port}")
                return True
                
        except Exception as e:
            logger.debug(f"❌ Fallback TCP falhou: {e}")
        
        return False
    
    def get_redirect_info(self):
        """NOVO: Retorna informações para o servidor de redirecionamento"""
        return {
            'current_ngrok': self.current_url,
            'history': list(self.ngrok_history.keys()),
            'timestamp': time.time()
        }
    
    def check_old_urls(self):
        """NOVO: Verifica se URLs antigas ainda estão ativas"""
        active_urls = []
        for url, info in self.ngrok_history.items():
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    active_urls.append(url)
            except:
                # URL não está mais ativa
                pass
        return active_urls

def sync_ngrok_instances():
    """Função principal de sincronização - VERSÃO MELHORADA"""
    coordinator = NgrokCoordinator()
    
    # ✅ VERIFICA SE JÁ EXISTE NGROK MANAGER ATIVO
    try:
        manager_check = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if manager_check.status_code == 200:
            logger.info("✅ NgrokManager já está ativo - Modo de sincronização")
    except:
        logger.info("🔧 Iniciando NgrokCoordinator standalone")
    
    # Inicia Ngrok se necessário
    url = coordinator.start_ngrok()
    
    if url:
        print(f"✅ Ngrok sincronizado - URL: {url}")
        print(f"🌐 Modo: {'Coordenador' if coordinator.current_pid else 'Monitor'}")
        print("🔄 Sistema multiporta ativado")
        print("📋 Histórico de URLs mantido")
        
        # ✅ INFORMAÇÕES DETALHADAS
        tunnels = coordinator.get_ngrok_tunnels() or {}
        print(f"📊 Túneis detectados: {len(tunnels)}")
        for name, tunnel_url in tunnels.items():
            status = "✅" if coordinator.verify_tunnel_health(tunnel_url, name) else "⚠️ "
            print(f"   {status} {name}: {tunnel_url}")
        
        # ✅ SINCRONIZA COM MANAGER
        coordinator.sync_with_ngrok_manager()
        
        # Inicia monitoramento contínuo
        try:
            coordinator.monitor_ngrok_url()
        except KeyboardInterrupt:
            print("\n⏹️  Monitoramento interrompido pelo usuário")
    else:
        print("❌ Falha na sincronização do Ngrok")

if __name__ == "__main__":
    sync_ngrok_instances()