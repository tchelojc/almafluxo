import time
import logging
from datetime import datetime, timedelta

class QuantumFallbackSystem:
    """Sistema de fallback para quando o Ngrok não está disponível"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_ngrok_check = datetime.now()
        self.ngrok_available = False
        
    def check_ngrok_availability(self):
        """Verifica se o Ngrok está disponível"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            self.ngrok_available = response.status_code == 200
            self.last_ngrok_check = datetime.now()
            return self.ngrok_available
        except:
            self.ngrok_available = False
            return False
            
    def get_fallback_url(self, local_port=5000):
        """Retorna URL de fallback"""
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"http://{local_ip}:{local_port}"
        except:
            return f"http://localhost:{local_port}"