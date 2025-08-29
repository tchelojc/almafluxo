"""
Monitor de conexão em tempo real para o sistema ALMA
"""

import threading
import time
from connection_manager import connection_manager

class ConnectionMonitor:
    """Monitora as conexões do sistema em tempo real"""
    
    def __init__(self, update_interval=10):
        self.update_interval = update_interval
        self.monitoring = False
        self.thread = None
        self.status_handlers = []
        
    def start_monitoring(self):
        """Inicia o monitoramento de conexões"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("🔍 Monitor de conexão iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento de conexões"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("🔍 Monitor de conexão parado")
    
    def add_status_handler(self, handler):
        """Adiciona um handler para receber atualizações de status"""
        self.status_handlers.append(handler)
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        last_status = None
        
        while self.monitoring:
            try:
                current_status = connection_manager.get_connection_status()
                
                # Notifica apenas se houve mudança significativa
                if last_status is None or self._status_changed(last_status, current_status):
                    for handler in self.status_handlers:
                        try:
                            handler(current_status)
                        except Exception as e:
                            print(f"Erro no handler de status: {e}")
                    
                    last_status = current_status
                
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Erro no monitor de conexão: {e}")
                time.sleep(5)
    
    def _status_changed(self, old_status, new_status):
        """Verifica se o status mudou significativamente"""
        # Compara as URLs e disponibilidades
        return (old_status['ngrok_url'] != new_status['ngrok_url'] or
                old_status['local_available'] != new_status['local_available'] or
                old_status['streamlit_available'] != new_status['streamlit_available'])

# Instância global do monitor
connection_monitor = ConnectionMonitor()