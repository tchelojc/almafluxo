# quantum_orchestrator.py
import threading
import time
import asyncio
import websockets
import logging
from datetime import datetime
from quantum_bridge import QuantumBridge

logger = logging.getLogger("QuantumOrchestrator")

class QuantumOrchestrator:
    def __init__(self):
        self.bridge = QuantumBridge()
        self.services = {}
        self.ws_server = None
        self.is_running = False
        
    def start_quantum_network(self):
        """Inicia a rede quântica entre todos os serviços"""
        logger.info("🌌 Iniciando rede quântica de comunicação...")
        
        try:
            # Iniciar WebSocket server para comunicação quântica
            self.is_running = True
            self.quantum_thread = threading.Thread(target=self.run_quantum_server)
            self.quantum_thread.daemon = True
            self.quantum_thread.start()
            
            # Registrar todos os serviços
            self.register_services()
            
            logger.info("✅ Rede quântica inicializada na porta 8765")
            return True
            
        except Exception as e:
            logger.error(f"❌ Falha ao iniciar rede quântica: {e}")
            return False
    
    def run_quantum_server(self):
        """Executa o servidor WebSocket em loop assíncrono"""
        async def server_loop():
            self.ws_server = await websockets.serve(
                self.bridge.handle_connection, 
                "localhost", 
                8765
            )
            await self.ws_server.wait_closed()
        
        asyncio.run(server_loop())
    
    def register_services(self):
        """Registra todos os serviços do sistema"""
        services = {
            'ngrok_coordinator': {
                'file': 'sync_ngrok.py',
                'port': 4040,
                'quantum_capable': True
            },
            'ngrok_manager': {
                'file': 'ngrok_manager.py',
                'port': 4041, 
                'quantum_capable': True
            },
            'flask_app': {
                'file': 'app.py',
                'port': 5000,
                'quantum_capable': True
            },
            'quantum_proxy': {
                'file': 'proxy_server.py',
                'port': 5500,
                'quantum_capable': True
            },
            'alma_server': {
                'file': 'server.py',
                'port': 8000,
                'quantum_capable': True
            }
        }
        
        for service_id, service_info in services.items():
            self.services[service_id] = {
                **service_info,
                'status': 'offline',
                'quantum_state': None,
                'last_heartbeat': None
            }
    
    def quantum_health_check(self):
        """Verificação de saúde da rede quântica"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'quantum_connections': len(self.bridge.connections),
            'entangled_pairs': len(self.bridge.entangled_pairs),
            'quantum_integrity': self.check_quantum_integrity()
        }
        
        for service_id, service_info in self.services.items():
            health_status['services'][service_id] = {
                'status': service_info['status'],
                'quantum_state': service_info['quantum_state'] is not None,
                'last_communication': service_info.get('last_heartbeat'),
                'quantum_capable': service_info['quantum_capable']
            }
        
        return health_status
    
    def check_quantum_integrity(self):
        """Verifica a integridade da rede quântica"""
        try:
            # Verificar se todos os serviços quânticos estão conectados
            quantum_services = [s for s in self.services.values() if s['quantum_capable']]
            connected_services = len(self.bridge.connections)
            
            integrity_score = connected_services / len(quantum_services) if quantum_services else 0
            
            return {
                'score': integrity_score,
                'status': 'optimal' if integrity_score >= 0.8 else 'degraded' if integrity_score >= 0.5 else 'critical',
                'connected_services': connected_services,
                'total_quantum_services': len(quantum_services)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de integridade: {e}")
            return {'score': 0, 'status': 'unknown', 'error': str(e)}
    
    def stop_quantum_network(self):
        """Para a rede quântica"""
        self.is_running = False
        if self.ws_server:
            self.ws_server.close()
        logger.info("🛑 Rede quântica encerrada")