#!/usr/bin/env python3
"""
🔧 ADMINISTRADOR PRINCIPAL DO SISTEMA FLUXON - VERSÃO COMPLETA
Gerencia todos os serviços incluindo Streamlit
"""

import time
import requests
import socket
import sys
import subprocess
import threading
import os
from pathlib import Path
import logging

# ==============================
# CONFIGURAÇÃO AVANÇADA
# ==============================

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("system_manager.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SystemManager")

BASE_DIR = Path(__file__).parent.parent

# ==============================
# STREAMLIT MANAGER (SEU CÓDIGO)
# ==============================

class StreamlitManager:
    def __init__(self):
        # Mapeamento de portas
        self.ports = {
            "streamlit_hub": 8501,
            "streamlit_daytrade": 8502,
            "streamlit_sports": 8503,
            "streamlit_quantum": 8504
        }

        # Caminhos absolutos dos apps Streamlit
        self.app_paths = {
            "streamlit_hub": BASE_DIR / "server" / "scripts" / "seletor" / "seletor.py",
            "streamlit_daytrade": BASE_DIR / "server" / "scripts" / "seletor" / "day_trade" / "project" / "main.py",
            "streamlit_sports": BASE_DIR / "server" / "scripts" / "seletor" / "project" / "main.py",
            "streamlit_quantum": BASE_DIR / "server" / "scripts" / "seletor" / "ApostaPro" / "main.py"
        }

        self.processes = {}

    def start_streamlit(self, app_name: str, port: int, headless: bool = True):
        """Inicia um aplicativo Streamlit específico"""
        app_path = self.app_paths.get(app_name)
        if not app_path or not app_path.exists():
            logger.error(f"Arquivo não encontrado: {app_path}")
            return None

        cmd = [
            "streamlit", "run", str(app_path),
            "--server.port", str(port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true" if headless else "false",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
        ]

        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'

        try:
            process = subprocess.Popen(
                cmd,
                cwd=app_path.parent,
                stdout=subprocess.DEVNULL if headless else None,
                stderr=subprocess.DEVNULL if headless else None,
                text=True,
                env=env
            )
        except Exception as e:
            logger.error(f"Erro ao iniciar {app_name}: {e}")
            return None

        # Aguarda para checar se o processo iniciou
        time.sleep(3)
        if process.poll() is None:
            self.processes[app_name] = process
            logger.info(f"{app_name} iniciado na porta {port} (PID: {process.pid})")
            return process
        else:
            logger.error(f"{app_name} falhou ao iniciar")
            return None

    def wait_for_streamlit(self, port: int, timeout: int = 30) -> bool:
        """Aguarda até que o Streamlit esteja respondendo"""
        start_time = time.time()
        url = f"http://localhost:{port}/_stcore/health"

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ Streamlit na porta {port} está online")
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)

        logger.error(f"❌ Timeout aguardando Streamlit na porta {port}")
        return False

# ==============================
# SERVIÇOS PRINCIPAIS
# ==============================

SERVICES = {
    "flask_api": {
        "port": 5000,
        "command": ["python", "app.py"],
        "cwd": BASE_DIR,
        "health_endpoint": "/api/health",
        "startup_time": 5,
        "max_retries": 3
    },
    "fastapi_proxy": {
        "port": 5001, 
        "command": ["python", "proxy_server.py"],
        "cwd": BASE_DIR,
        "health_endpoint": "/health",
        "startup_time": 3,
        "max_retries": 3
    }
}

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def is_port_in_use(port: int) -> bool:
    """Verifica se a porta está em uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_service_health(port: int, endpoint: str = "") -> bool:
    """Verifica se o serviço está saudável"""
    for attempt in range(3):
        try:
            response = requests.get(f"http://127.0.0.1:{port}{endpoint}", timeout=2)
            if response.status_code == 200:
                return True
        except:
            time.sleep(0.5)
    return False

def start_service(name: str, config: dict):
    """Inicia um serviço"""
    logger.info(f"Iniciando serviço {name}...")
    
    if is_port_in_use(config["port"]):
        logger.warning(f"Porta {config['port']} já está em uso para {name}")
        return None
    
    try:
        process = subprocess.Popen(
            config["command"],
            cwd=config["cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        startup_time = config.get("startup_time", 5)
        for i in range(startup_time * 2):
            time.sleep(0.5)
            if check_service_health(config["port"], config.get("health_endpoint", "")):
                logger.info(f"Serviço {name} iniciado com sucesso na porta {config['port']}")
                return process
                
        logger.error(f"Serviço {name} não responde após {startup_time} segundos")
        process.terminate()
        return None
        
    except Exception as e:
        logger.error(f"Erro ao iniciar {name}: {e}")
        return None

# ==============================
# ADMINISTRADOR PRINCIPAL
# ==============================

class SystemManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.service_status = {}
        self.retry_count = {}
        self.streamlit_manager = StreamlitManager()
        
        # Inicializar contadores
        for name in list(SERVICES.keys()) + list(self.streamlit_manager.ports.keys()):
            self.retry_count[name] = 0
        
    def start_all_services(self):
        """Inicia todos os serviços em ordem controlada"""
        logger.info("Iniciando sistema FLUXON...")
        
        # 1. Iniciar serviços principais
        service_order = ["flask_api", "fastapi_proxy"]
        
        for service_name in service_order:
            if service_name in SERVICES:
                config = SERVICES[service_name]
                process = start_service(service_name, config)
                self.processes[service_name] = process
                
                is_healthy = process is not None and check_service_health(
                    config["port"], config.get("health_endpoint", "")
                )
                self.service_status[service_name] = is_healthy
                
                if not is_healthy and process:
                    logger.warning(f"Serviço {service_name} iniciado mas não está saudável")
        
        # 2. Iniciar Streamlit apps
        logger.info("Iniciando aplicações Streamlit...")
        
        # Primeiro o hub (mais importante)
        hub_process = self.streamlit_manager.start_streamlit(
            "streamlit_hub", 
            self.streamlit_manager.ports["streamlit_hub"], 
            headless=False
        )
        
        if hub_process:
            self.processes["streamlit_hub"] = hub_process
            if self.streamlit_manager.wait_for_streamlit(self.streamlit_manager.ports["streamlit_hub"]):
                self.service_status["streamlit_hub"] = True
            else:
                self.service_status["streamlit_hub"] = False
        
        # Depois os outros apps
        for app_name, port in self.streamlit_manager.ports.items():
            if app_name != "streamlit_hub":
                process = self.streamlit_manager.start_streamlit(app_name, port, headless=True)
                if process:
                    self.processes[app_name] = process
                    self.service_status[app_name] = True
                    time.sleep(2)
        
        logger.info("Todos os serviços iniciados")
        self.print_status()
    
    def monitor_services(self):
        """Monitora e reinicia serviços se necessário"""
        logger.info("Iniciando monitoramento de serviços...")
        
        while self.running:
            try:
                all_healthy = True
                
                # Monitorar serviços principais
                for service_name, config in SERVICES.items():
                    is_healthy = check_service_health(config["port"], config.get("health_endpoint", ""))
                    self.update_service_status(service_name, is_healthy, config)
                    if not is_healthy:
                        all_healthy = False
                
                # Monitorar Streamlit apps
                for app_name, port in self.streamlit_manager.ports.items():
                    is_healthy = check_service_health(port, "/_stcore/health")
                    self.update_service_status(app_name, is_healthy, {"max_retries": 3})
                    if not is_healthy:
                        all_healthy = False
                
                if all_healthy:
                    logger.info("Todos os serviços estão operacionais")
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Interrupção recebida, desligando sistema...")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(10)
    
    def update_service_status(self, service_name: str, is_healthy: bool, config: dict):
        """Atualiza status do serviço e reinicia se necessário"""
        previous_status = self.service_status.get(service_name, False)
        self.service_status[service_name] = is_healthy
        
        if not is_healthy:
            logger.warning(f"Serviço {service_name} está offline")
            
            if self.retry_count[service_name] < config.get("max_retries", 3):
                self.retry_count[service_name] += 1
                logger.info(f"Tentativa {self.retry_count[service_name]} de reiniciar {service_name}")
                
                # Encerrar processo anterior
                if service_name in self.processes and self.processes[service_name]:
                    try:
                        self.processes[service_name].terminate()
                        self.processes[service_name].wait(timeout=5)
                    except:
                        pass
                
                # Reiniciar serviço
                if service_name in SERVICES:
                    self.processes[service_name] = start_service(service_name, SERVICES[service_name])
                elif service_name in self.streamlit_manager.ports:
                    self.processes[service_name] = self.streamlit_manager.start_streamlit(
                        service_name, 
                        self.streamlit_manager.ports[service_name],
                        headless=(service_name != "streamlit_hub")
                    )
            else:
                logger.error(f"Serviço {service_name} excedeu o número máximo de tentativas")
        else:
            if not previous_status and is_healthy:
                logger.info(f"Serviço {service_name} recuperado")
            self.retry_count[service_name] = 0
    
    def print_status(self):
        """Exibe status atual dos serviços"""
        print("\n" + "="*60)
        print("🔄 STATUS DO SISTEMA FLUXON")
        print("="*60)
        
        # Serviços principais
        for service_name, config in SERVICES.items():
            status = "✅ ONLINE" if self.service_status.get(service_name, False) else "❌ OFFLINE"
            print(f"{status} {service_name} (porta {config['port']})")
        
        # Streamlit apps
        for app_name, port in self.streamlit_manager.ports.items():
            status = "✅ ONLINE" if self.service_status.get(app_name, False) else "❌ OFFLINE"
            print(f"{status} {app_name} (porta {port})")
        
        print("="*60)
    
    def shutdown(self):
        """Desliga todos os serviços de forma controlada"""
        self.running = False
        logger.info("Desligando todos os serviços...")
        
        for name, process in self.processes.items():
            if process:
                try:
                    logger.info(f"Encerrando {name}...")
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
        
        logger.info("Sistema desligado com sucesso")

def main():
    """Função principal"""
    manager = SystemManager()
    
    try:
        manager.start_all_services()
        manager.monitor_services()
    except KeyboardInterrupt:
        manager.shutdown()
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        manager.shutdown()

if __name__ == "__main__":
    main()