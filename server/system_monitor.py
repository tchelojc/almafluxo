# system_monitor.py
import time
import requests
import logging
import subprocess
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SystemMonitor')

class SystemMonitor:
    def __init__(self):
        self.running = True
        
    def check_ngrok_health(self):
        """Verifica a saúde do Ngrok"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            return response.status_code == 200
        except:
            return False
        
    def check_ngrok_stability(self):
        """Verifica estabilidade do Ngrok com testes rigorosos"""
        try:
            # Teste 1: API do Ngrok
            api_response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if api_response.status_code != 200:
                return False, "API não responde"
            
            # Teste 2: Túneis ativos
            tunnels = api_response.json().get('tunnels', [])
            if not tunnels:
                return False, "Nenhum túnel ativo"
            
            # Teste 3: URL pública responde
            public_url = tunnels[0]['public_url']
            for i in range(3):  # Testa 3 vezes
                try:
                    health_response = requests.get(f"{public_url}/health", timeout=5)
                    if health_response.status_code == 200:
                        return True, f"Estável: {public_url}"
                except:
                    if i == 2:  # Última tentativa
                        return False, f"URL não responde: {public_url}"
                    time.sleep(1)
                    
            return False, "Falha nos testes de estabilidade"
            
        except Exception as e:
            return False, f"Erro: {str(e)}"
            
    def check_flask_health(self):
        """Verifica a saúde do Flask"""
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def restart_ngrok(self):
        """Reinicia o Ngrok"""
        try:
            logger.warning("Reiniciando Ngrok...")
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
            time.sleep(2)
            subprocess.Popen(["ngrok", "http", "5000", "--log=stdout"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Ngrok reiniciado")
            return True
        except Exception as e:
            logger.error(f"Erro ao reiniciar Ngrok: {e}")
            return False
            
    def monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                # Verifica saúde dos componentes
                ngrok_healthy = self.check_ngrok_health()
                flask_healthy = self.check_flask_health()
                
                if not ngrok_healthy and flask_healthy:
                    logger.warning("Ngrok não está saudável, mas Flask está - reiniciando Ngrok")
                    self.restart_ngrok()
                    
                elif not flask_healthy:
                    logger.error("Flask não está respondendo - verifique o servidor")
                    
                time.sleep(30)  # Verifica a cada 30 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitor: {e}")
                time.sleep(60)
                
    def start(self):
        """Inicia o monitoramento em thread separada"""
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Monitor do sistema iniciado")
        
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        logger.info("Monitor do sistema parado")

# Uso:
# monitor = SystemMonitor()
# monitor.start()