from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta, timezone
import socket
import struct
import os
import requests
import platform
import time
from typing import Optional, Dict

class TimeValidator:
    def __init__(self):
        self.tf = TimezoneFinder()
        self.timeout = 3
        self.last_error = None
        self.time_servers = [
            "time.google.com",
            "time.windows.com",
            "time.apple.com",
            "pool.ntp.org",
            "a.ntp.br",
            "b.ntp.br"
        ]
        self.allowed_drift = timedelta(minutes=5)  # 5 minutos de tolerância
        self.api_time_servers = [
            "http://worldtimeapi.org/api/ip",
            "http://worldclockapi.com/api/json/utc/now"
        ]

    def _query_ntp_server(self, server):
        """Consulta um servidor NTP específico para obter o tempo"""
        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(self.timeout)
            
            ntp_packet = bytearray(48)
            ntp_packet[0] = 0x1B  # LI, Version, Mode
            
            client.sendto(ntp_packet, (server, 123))
            data, _ = client.recvfrom(1024)
            
            if data:
                unpacked = struct.unpack('!12I', data)
                ntp_time = unpacked[10] - 2208988800
                return datetime.fromtimestamp(ntp_time, timezone.utc)
                
        except socket.timeout:
            print(f"Timeout ao acessar servidor NTP: {server}")
            raise
        except Exception as e:
            print(f"Erro ao acessar servidor NTP {server}: {str(e)}")
            raise
        finally:
            if client:
                client.close()

    def _get_api_time(self):
        """Obtém tempo de APIs HTTP com fallback"""
        for api_url in self.api_time_servers:
            try:
                response = requests.get(api_url, timeout=self.timeout)
                if response.ok:
                    if 'worldtimeapi' in api_url:
                        return datetime.fromisoformat(response.json()['datetime'].replace('Z', '+00:00'))
                    elif 'worldclockapi' in api_url:
                        return datetime.strptime(
                            response.json()['currentDateTime'], 
                            "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)
            except Exception as e:
                print(f"⚠️ Falha na API {api_url}: {str(e)}")
                continue
        return None

    def get_network_time(self):
        """Obtém tempo com múltiplos fallbacks"""
        # 1. Tenta APIs HTTP primeiro
        api_time = self._get_api_time()
        if api_time:
            return api_time
            
        # 2. Tenta servidores NTP
        ntp_time = self._get_ntp_time_with_fallback()
        if ntp_time:
            return ntp_time
            
        # 3. Fallback final
        print("⚠️ Todas as fontes de tempo falharam - usando horário local como fallback")
        return datetime.now(timezone.utc)

    def _get_ntp_time_with_fallback(self):
        """Tenta múltiplos servidores NTP"""
        for server in self.time_servers:
            try:
                return self._query_ntp_server(server)
            except Exception as e:
                print(f"⚠️ Falha no servidor {server}: {str(e)}")
                continue
        return None

    def validate_time(self, local_time=None) -> Dict[str, bool]:
        """Validação com tratamento robusto de erros"""
        try:
            if local_time is None:
                local_time = datetime.now(timezone.utc)
            elif not local_time.tzinfo:
                local_time = local_time.replace(tzinfo=timezone.utc)

            server_time = self.get_network_time()
            
            if not server_time:
                return {
                    "valid": True, 
                    "message": "Não foi possível verificar - usando horário local",
                    "status": "WARNING"
                }
            
            time_diff = abs((server_time - local_time))
            
            if time_diff > self.allowed_drift:
                return {
                    "valid": False,
                    "message": f"Diferença temporal detectada: {time_diff} (limite: {self.allowed_drift})",
                    "local_time": local_time,
                    "server_time": server_time,
                    "status": "ERROR",
                    "error": "TIME_DESYNC"
                }
            
            return {
                "valid": True, 
                "message": "Horário sincronizado",
                "status": "OK",
                "local_time": local_time,
                "server_time": server_time
            }
        except Exception as e:
            return {
                "valid": True,  # Permite continuar mesmo com erro
                "message": f"Erro na verificação: {str(e)} - Continuando com horário local",
                "status": "WARNING",
                "error": str(e)
            }

class QuantumTimeAdjuster:
    def __init__(self):
        self.time_servers = [
            'time.google.com',
            'time.windows.com',
            'pool.ntp.org',
            'a.ntp.br',
            'b.ntp.br'
        ]
        self.api_time_servers = [
            'http://worldtimeapi.org/api/ip',
            'http://worldclockapi.com/api/json/utc/now'
        ]
        self.allowed_drift = timedelta(minutes=5)
        self.last_known_good_time = datetime.now(timezone.utc)
        self.timeout = 3
        self.max_retries = 2

    def _query_ntp_server(self, server: str) -> Optional[datetime]:
        """Consulta segura a servidores NTP"""
        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(self.timeout)
            ntp_packet = bytearray(48)
            ntp_packet[0] = 0x1B
            client.sendto(ntp_packet, (server, 123))
            data, _ = client.recvfrom(1024)
            if data:
                unpacked = struct.unpack('!12I', data)
                return datetime.fromtimestamp(unpacked[10] - 2208988800, timezone.utc)
        except Exception as e:
            print(f"⚠️ Falha no servidor {server}: {str(e)}")
        finally:
            if client:
                client.close()
        return None

    def _get_api_time(self) -> Optional[datetime]:
        """Obtém tempo de APIs HTTP"""
        for api_url in self.api_time_servers:
            try:
                response = requests.get(api_url, timeout=self.timeout)
                if response.ok:
                    if 'worldtimeapi' in api_url:
                        return datetime.fromisoformat(response.json()['datetime'].replace('Z', '+00:00'))
                    elif 'worldclockapi' in api_url:
                        return datetime.strptime(
                            response.json()['currentDateTime'], 
                            "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)
            except Exception as e:
                print(f"⚠️ Falha na API {api_url}: {str(e)}")
        return None

    def get_network_time(self) -> datetime:
        """Obtém tempo com múltiplos fallbacks"""
        # 1. Tenta APIs HTTP primeiro
        api_time = self._get_api_time()
        if api_time:
            self.last_known_good_time = api_time
            return api_time
            
        # 2. Tenta servidores NTP
        for server in self.time_servers:
            for attempt in range(self.max_retries):
                try:
                    if time := self._query_ntp_server(server):
                        self.last_known_good_time = time
                        return time
                except Exception as e:
                    print(f"⚠️ Tentativa {attempt+1} com {server} falhou: {str(e)}")
                    time.sleep(0.5)
        
        print("⚠️ Todas as fontes de tempo falharam - usando horário local com aviso")
        return self.last_known_good_time + (datetime.now(timezone.utc) - self.last_known_good_time)

    def validate_time(self) -> Dict[str, bool]:
        """Validação tolerante a falhas"""
        try:
            local_time = datetime.now(timezone.utc)
            network_time = self.get_network_time()
            
            drift = abs(network_time - local_time)
            is_valid = drift <= self.allowed_drift
            
            return {
                'valid': is_valid,
                'message': 'Tempo sincronizado' if is_valid else f'Diferença temporal: {drift}',
                'local_time': local_time,
                'server_time': network_time,
                'drift': drift,
                'status': 'OK' if is_valid else 'DESINCRONIZADO'
            }
            
        except Exception as e:
            print(f"⚠️ Erro crítico na validação: {str(e)}")
            return {
                'valid': True,
                'message': f'Erro na verificação: {str(e)} - Continuando com horário local',
                'status': 'WARNING',
                'error': str(e)
            }