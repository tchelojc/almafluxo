import requests
import datetime
import os
import logging
import sys

def sync_time_with_server():
    """Sincroniza o horário com o servidor"""
    try:
        # Tenta conectar com o servidor local
        response = requests.get('http://localhost:5000/api/debug/timezone', timeout=5)
        if response.status_code == 200:
            data = response.json()
            server_time_str = data['server_time_utc']
            
            # Converte para datetime (tratando diferentes formatos)
            if server_time_str.endswith('Z'):
                server_time = datetime.datetime.fromisoformat(server_time_str.replace('Z', '+00:00'))
            else:
                server_time = datetime.datetime.fromisoformat(server_time_str)
                
            local_time = datetime.datetime.now(datetime.timezone.utc)
            
            time_diff = (server_time - local_time).total_seconds() / 3600
            print(f"⏰ Diferença de horário: {time_diff:.2f} horas")
            
            if abs(time_diff) > 1:  # Mais de 1 hora de diferença
                print("⚠️  AVISO: Grande diferença de horário detectada!")
                print(f"   Servidor UTC: {server_time}")
                print(f"   Local UTC: {local_time}")
                print("   Isso pode causar problemas de autenticação.")
                return False
            return True
    except requests.exceptions.ConnectionError:
        print("ℹ️  Servidor não está respondendo (pode ser normal durante inicialização)")
        return True
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        return True

if __name__ == "__main__":
    success = sync_time_with_server()
    sys.exit(0 if success else 1)