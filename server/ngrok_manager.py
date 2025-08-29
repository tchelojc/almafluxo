# ngrok_manager.py - VERSÃO MULTIPORTAS
import time
import requests
import logging
from bridge_config import bridge_config
from threading import Event
import json
from pathlib import Path

class NgrokManager:
    def __init__(self):
        self._is_running = True
        self._stop_event = Event()
        self._current_urls = {}
        self._failed_checks = {}
        self._max_failed_checks = 3
        self._max_recovery_attempts = 5  # ✅ ADICIONE ESTA LINHA
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = Path(__file__).parent / ".ngrok_coordinator.json"
        self.redirect_config_file = Path(__file__).parent / ".ngrok_redirects.json"
        
        # Configurações
        self._monitor_interval = 20
        self._request_timeout = 12

    # ✅ ADICIONE ESTA FUNÇÃO PARA VERIFICAÇÃO DE TIMEZONE
    def check_timezone_compatibility(self):
        """Verifica compatibilidade de timezone com o servidor Flask"""
        try:
            response = requests.get("http://localhost:5000/api/timezone/debug", timeout=5)
            if response.status_code == 200:
                timezone_info = response.json()
                
                # ✅ VERIFICA DIFERENÇAS CRÍTICAS
                timezone_offset = timezone_info.get('timezone_offset', 0)
                token_leeway = timezone_info.get('token_leeway', 0)
                
                if abs(timezone_offset) > 3:  # Mais de 3 horas de diferença
                    self.logger.warning(
                        f"🚨 Grande diferença de timezone: {timezone_offset:.1f}h "
                        f"(leeway: {token_leeway/3600:.1f}h)"
                    )
                    return False
                
                self.logger.debug(
                    f"🌐 Timezone OK: offset={timezone_offset:.1f}h, "
                    f"leeway={token_leeway/3600:.1f}h"
                )
                return True
                
        except requests.exceptions.ConnectionError:
            self.logger.debug("⚠️  Servidor Flask não disponível para verificação de timezone")
            return True  # Não é crítico se o Flask não estiver rodando
        except Exception as e:
            self.logger.warning(f"⚠️  Erro na verificação de timezone: {e}")
            return True  # Continua operação mesmo com erro
            
        return True

    # ✅ ADICIONE ESTA FUNÇÃO PARA MONITORAMENTO COM TIMEZONE
    def monitor_ngrok_url(self):
        """Monitora continuamente a URL do Ngrok - VERSÃO MELHORADA"""
        self.logger.info("📡 Iniciando monitoramento contínuo multiporta...")
        
        # ✅ VERIFICAÇÃO DE TIMEZONE CRÍTICA
        if not self.check_timezone_compatibility():
            self.logger.warning("🚨 ALERTA: Possível problema de timezone detectado!")
        
        last_tunnels = {}
        performance_metrics = {
            'checks_total': 0,
            'checks_failed': 0,
            'recovery_attempts': 0,
            'url_changes': 0,
            'start_time': time.time()
        }
        
        while self._is_running:
            try:
                performance_metrics['checks_total'] += 1
                new_urls = self.fetch_ngrok_urls()
                
                # ✅ VERIFICAÇÃO PERIÓDICA DE TIMEZONE (a cada 10 ciclos)
                if performance_metrics['checks_total'] % 10 == 0:
                    if not self.check_timezone_compatibility():
                        self.logger.warning("🔄 Timezone problem detectado - re-verificando túneis")
                
                # ✅ VERIFICAÇÃO INTELIGENTE COM TOLERÂNCIA A FALHAS
                verified_urls = {}
                
                for name, url in new_urls.items():
                    is_working = self.verify_connection(url)
                    
                    if is_working:
                        verified_urls[name] = url
                        self._failed_checks[name] = 0
                    else:
                        failed_count = self._failed_checks.get(name, 0) + 1
                        self._failed_checks[name] = failed_count
                        
                        if failed_count <= self._max_failed_checks:
                            self.logger.debug(f"⚠️  {name} falhou {failed_count}/{self._max_failed_checks}: {url}")
                            verified_urls[name] = url
                        else:
                            self.logger.warning(f"❌ {name} removido após {failed_count} falhas: {url}")
                
                # Verifica se houve mudanças significativas
                if verified_urls != self._current_urls:
                    if verified_urls:
                        self.logger.info(f"🔄 Mudança detectada: {len(verified_urls)} túneis ativos")
                        self._current_urls = verified_urls
                        performance_metrics['url_changes'] += 1
                        
                        self.update_bridge_config(verified_urls)
                        self.update_redirect_config(verified_urls.get('proxy'))
                    else:
                        self.logger.warning("⚠️  Todos os túneis inativos - aguardando recuperação")
                        self._current_urls = {}
                        self.update_redirect_config(None)
                
                self.log_urls_status(verified_urls)
                
                # ✅ REGISTRA MÉTRICAS A CADA 10 CICLOS
                if performance_metrics['checks_total'] % 10 == 0:
                    uptime = time.time() - performance_metrics['start_time']
                    success_rate = (
                        (performance_metrics['checks_total'] - performance_metrics['checks_failed']) / 
                        performance_metrics['checks_total']
                    ) * 100
                    
                    self.logger.info(
                        f"📈 Métricas: {uptime:.0f}s uptime, "
                        f"{success_rate:.1f}% sucesso, "
                        f"{performance_metrics['url_changes']} mudanças detectadas"
                    )
                        
            except Exception as e:
                performance_metrics['checks_failed'] += 1
                self.logger.error(f"❌ Erro no monitoramento: {str(e)}")
                
                if performance_metrics['recovery_attempts'] < self._max_recovery_attempts:
                    performance_metrics['recovery_attempts'] += 1
                    self.logger.warning(
                        f"🔄 Tentativa de recuperação "
                        f"{performance_metrics['recovery_attempts']}/{self._max_recovery_attempts}"
                    )
                    self.attempt_recovery()
                else:
                    self.logger.critical("💥 Máximo de tentativas de recuperação excedido")
                
                time.sleep(30)
            
            self._stop_event.wait(self._monitor_interval)

    # ✅ MODIFIQUE A FUNÇÃO start_monitoring PARA USAR A NOVA VERSÃO
    def start_monitoring(self):
        """Inicia o monitoramento com a nova versão"""
        self.monitor_ngrok_url()

    def get_coordinator_urls(self):
        """Obtém URLs do arquivo de coordenação - AGORA retorna dicionário"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('urls', {})  # ✅ Retorna dicionário
        except:
            pass
        return {}

    def update_redirect_config(self, url):
        """Atualiza arquivo de configuração do redirect server"""
        try:
            config = {'current_ngrok': url}
            with open(self.redirect_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self.logger.info(f"✅ Configuração de redirect atualizada: {url}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar redirect config: {e}")

    def fetch_ngrok_urls(self):
        """Obtém TODOS os túneis Ngrok ativos - VERSÃO MAIS ROBUSTA"""
        urls = {}
        
        try:
            # ✅ TENTA MÚLTIPLAS PORTAS DA API NGROK
            ngrok_ports = [4040, 4041, 4050]  # Portas possíveis do Ngrok
            
            for port in ngrok_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/api/tunnels", timeout=3)
                    if response.status_code == 200:
                        tunnels = response.json().get('tunnels', [])
                        
                        for tunnel in tunnels:
                            if tunnel.get('proto') == 'https':
                                public_url = tunnel['public_url']
                                config_addr = tunnel.get('config', {}).get('addr', '')
                                tunnel_name = tunnel.get('name', '')
                                
                                # ✅ IDENTIFICAÇÃO MAIS INTELIGENTE
                                if ':5000' in config_addr or 'proxy' in tunnel_name.lower():
                                    urls['proxy'] = public_url
                                elif ':8501' in config_addr or 'streamlit' in tunnel_name.lower():
                                    urls['streamlit'] = public_url
                                elif ':5500' in config_addr or 'quantum' in tunnel_name.lower():
                                    urls['quantum_proxy'] = public_url
                                elif ':5001' in config_addr or 'redirect' in tunnel_name.lower():
                                    urls['redirect'] = public_url
                                else:
                                    # Nome automático baseado na porta
                                    port_match = re.search(r':(\d+)', config_addr)
                                    if port_match:
                                        port_num = port_match.group(1)
                                        urls[f'port_{port_num}'] = public_url
                                    else:
                                        urls[f'tunnel_{len(urls)}'] = public_url
                        
                        break  # Se encontrou em uma porta, para de procurar
                        
                except requests.exceptions.ConnectionError:
                    continue  # Porta não disponível, tenta próxima
                except Exception as e:
                    self.logger.debug(f"Erro na porta {port}: {e}")
                    continue
            
            # ✅ PRIORIDADE: URLs do coordenador (se existirem)
            coordinator_urls = self.get_coordinator_urls()
            if coordinator_urls:
                urls.update(coordinator_urls)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar URLs Ngrok: {e}")
        
        return urls

    def verify_connection(self, url, path='/health'):
        """Verifica se a URL está respondendo - VERSÃO ULTRA ROBUSTA"""
        if not url:
            return False
        
        # ✅ ADICIONA VERIFICAÇÃO DE DOMÍNIO NGROK VÁLIDO
        if 'ngrok-free.app' not in url and 'ngrok.io' not in url:
            self.logger.debug(f"URL não é Ngrok: {url}")
            return False
        
        # ✅ LISTA COMPLETA DE PATHS PARA TESTE
        test_paths = [
            '/health',
            '/',
            '/api/status', 
            '/proxy/streamlit/_stcore/health',
            '/login',
            '/api/streamlit/status'
        ]
        
        for test_path in test_paths:
            try:
                test_url = f"{url.rstrip('/')}{test_path}"
                
                # ✅ HEADERS MELHORADOS
                headers = {
                    'X-Fluxon-Verification': 'true',
                    'User-Agent': 'NgrokManager/2.0',
                    'ngrok-skip-browser-warning': 'true',
                    'Accept': '*/*',
                    'Cache-Control': 'no-cache'
                }
                
                response = requests.get(
                    test_url,
                    headers=headers,
                    timeout=15,  # ✅ AUMENTADO PARA 15s
                    allow_redirects=True,
                    verify=False  # ✅ DESABILITA VERIFICAÇÃO SSL PARA TESTE
                )
                
                # ✅ CRITÉRIO EXTREMAMENTE FLEXÍVEL
                # Qualquer resposta HTTP entre 200-499 é considerada sucesso
                if 200 <= response.status_code < 500:
                    self.logger.debug(f"✅ {test_url} respondendo: {response.status_code}")
                    return True
                    
            except requests.exceptions.Timeout:
                self.logger.debug(f"⏰ Timeout em {test_url}")
                continue
            except requests.exceptions.ConnectionError:
                self.logger.debug(f"🔌 Connection error em {test_url}")
                continue
            except requests.exceptions.SSLError:
                self.logger.debug(f"🔒 SSL error em {test_url} (ignorado)")
                continue
            except Exception as e:
                self.logger.debug(f"❌ Erro em {test_url}: {e}")
                continue
        
        # ✅ FALLBACK AVANÇADO
        try:
            from urllib.parse import urlparse
            import socket
            
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            # Teste de conexão TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                self.logger.debug(f"✅ Conexão TCP bem-sucedida: {hostname}:{port}")
                return True
                
        except Exception as e:
            self.logger.debug(f"❌ Fallback TCP falhou: {e}")
        
        return False

    def update_bridge_config(self, urls):
        """Atualiza bridge config e compartilha com outros componentes"""
        try:
            # Prioridade: proxy → streamlit → primeira URL disponível
            main_url = urls.get('proxy') or urls.get('streamlit') or next(iter(urls.values()), None)
            
            if main_url:
                bridge_config.update_ngrok_url(main_url)
                self.logger.info(f"🌐 URL principal atualizada: {main_url}")
            
            # ✅ ATUALIZA CONFIGURAÇÃO INTERNA
            bridge_config.urls = urls
            bridge_config.config['urls'] = urls
            bridge_config.config['last_updated'] = time.time()
            
            # ✅ COMPARTILHA COM REDIRECT SERVER
            self.share_config_with_redirect_server(urls)
            
            # ✅ SALVA CONFIGURAÇÃO
            if hasattr(bridge_config, 'save'):
                bridge_config.save()
            else:
                import json
                with open('bridge_config.json', 'w', encoding='utf-8') as f:
                    json.dump(bridge_config.config, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar bridge config: {e}")

    def log_urls_status(self, urls):
        """Log do status de todas as URLs - VERSÃO SILENCIOSA"""
        if not urls:
            self.logger.warning("❌ Nenhum túnel Ngrok ativo")
            return
            
        # ✅ LOG APENAS SE HOUVER MUDANÇAS OU ERROS
        active_urls = []
        problematic_urls = []
        
        for name, url in urls.items():
            is_working = self.verify_connection(url)
            if is_working:
                active_urls.append((name, url))
            else:
                problematic_urls.append((name, url))
        
        if active_urls:
            self.logger.info("📊 Túneis ativos:")
            for name, url in active_urls:
                self.logger.info(f"   ✅ {name}: {url}")
        
        if problematic_urls:
            self.logger.warning("⚠️  Túneis com problemas:")
            for name, url in problematic_urls:
                failed_count = self._failed_checks.get(name, 0)
                self.logger.warning(f"   ❌ {name}: {url} (falhas: {failed_count})")

    def share_config_with_redirect_server(self, urls):
        """Compartilha a configuração com o Redirect Server"""
        try:
            redirect_config_file = Path(__file__).parent.parent / "client" / ".ngrok_redirects.json"
            main_url = urls.get('proxy') or urls.get('streamlit') or next(iter(urls.values()), None)
            
            config = {
                'current_ngrok': main_url,
                'urls': urls,
                'last_updated': time.time(),
                'source': 'ngrok_manager'
            }
            
            with open(redirect_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"✅ Configuração compartilhada com Redirect Server: {main_url}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao compartilhar config: {e}")
        
    def attempt_recovery(self):
        """Tenta recuperação de túneis inativos - VERSÃO MAIS AGRESSIVA"""
        self.logger.info("🔄 Tentando recuperação agressiva de túneis...")
        
        # ✅ TENTA MÚLTIPLAS ESTRATÉGIAS DE RECUPERAÇÃO
        
        # 1. Força nova detecção
        new_urls = self.fetch_ngrok_urls()
        
        # 2. Se não encontrou, tenta reiniciar processos Ngrok
        if not new_urls:
            self.logger.warning("🔧 Nenhum túnel encontrado, tentando reinicialização...")
            try:
                self.restart_ngrok_processes()
                time.sleep(10)  # Aguarda inicialização
                new_urls = self.fetch_ngrok_urls()
            except Exception as e:
                self.logger.error(f"❌ Falha na reinicialização: {e}")
        
        if new_urls:
            self.logger.info(f"🎯 Recuperação bem-sucedida: {len(new_urls)} túneis")
            self._current_urls = new_urls
            self.update_bridge_config(new_urls)
            self.update_redirect_config(new_urls.get('proxy'))
            
            # ✅ RESETA CONTADORES DE FALHA
            for name in new_urls.keys():
                self._failed_checks[name] = 0
        else:
            self.logger.critical("💥 Recuperação falhou - nenhum túnel ativo")

    def restart_ngrok_processes(self):
        """Reinicia processos Ngrok - CORREÇÃO PARA WINDOWS"""
        try:
            import platform
            if platform.system() == "Windows":
                # Windows
                import subprocess
                subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], 
                            capture_output=True, shell=True)
                time.sleep(2)
                # Inicia novo processo em background
                subprocess.Popen(["ngrok", "http", "5000", "--log=stdout"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Linux/Mac
                import subprocess
                subprocess.run(["pkill", "-9", "-f", "ngrok"], 
                            capture_output=True)
                time.sleep(2)
                subprocess.Popen(["ngrok", "http", "5000", "--log=stdout"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            self.logger.info("✅ Processos Ngrok reiniciados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao reiniciar Ngrok: {e}")
            raise

    def stop(self):
        """Para o monitoramento"""
        self.logger.info("🛑 Stopping Ngrok monitoring...")
        self._is_running = False
        self._stop_event.set()

# ✅ ADAPTAÇÃO DO BRIDGE_CONFIG PARA MULTIPORTAS - VERSÃO CORRIGIDA
def enhance_bridge_config():
    """Adiciona funcionalidade multiportas ao bridge_config existente"""
    if not hasattr(bridge_config, 'urls'):
        bridge_config.urls = {}
    
    if not hasattr(bridge_config, 'update_urls'):
        def update_urls(self, urls_dict):
            """Atualiza múltiplas URLs - VERSÃO CORRIGIDA"""
            self.urls = urls_dict
            self.config['urls'] = urls_dict
            self.config['last_updated'] = time.time()
            
            # ✅ CORREÇÃO: Salva usando o método existente do bridge_config
            try:
                # Tenta o método save() se existir
                if hasattr(self, 'save'):
                    self.save()
                # Ou salva manualmente se não existir
                else:
                    import json
                    with open('bridge_config.json', 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=2)
            except Exception as e:
                self.logger.error(f"Erro ao salvar configuração: {e}")
        
        bridge_config.update_urls = update_urls.__get__(bridge_config)
    
    if not hasattr(bridge_config, 'get_url'):
        def get_url(self, name):
            """Obtém URL específica por nome"""
            return self.urls.get(name)
        
        bridge_config.get_url = get_url.__get__(bridge_config)
    
    # ✅ ADICIONA MÉTODO save_config SE NÃO EXISTIR
    if not hasattr(bridge_config, 'save_config'):
        def save_config(self):
            """Método para salvar configuração - VERSÃO CORRIGIDA"""
            try:
                import json
                with open('bridge_config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
            except Exception as e:
                self.logger.error(f"Erro ao salvar configuração: {e}")
        
        bridge_config.save_config = save_config.__get__(bridge_config)

# ✅ MODIFIQUE O BLOCO PRINCIPAL
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    manager = NgrokManager()
    print("🔍 Ngrok Multi-Port Monitor initialized. Press Ctrl+C to stop.")
    
    try:
        # ✅ VERIFICAÇÃO INICIAL DE TIMEZONE
        if not manager.check_timezone_compatibility():
            print("⚠️  AVISO: Diferença de timezone detectada. Tokens podem expirar prematuramente.")
        
        manager.start_monitoring()
    except KeyboardInterrupt:
        manager.stop()
        print("🛑 Monitoring stopped gracefully")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        manager.stop()