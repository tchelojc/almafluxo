import requests
import uuid
import hmac
import os
from datetime import datetime

def calcular_hash(license_key, device_id, app_name, secret_key):
    """Calcula o hash de segurança de forma consistente"""
    message = f"{license_key}{device_id}{app_name}".encode('utf-8')
    return hmac.new(
        secret_key.encode('utf-8'),
        message,
        'sha256'
    ).hexdigest()

def testar_conexao_servidor():
    """Testa a comunicação com todas as rotas do servidor"""
    print("\n=== TESTE DE CONEXÃO COM SERVIDOR ===")
    
    # Configurações - devem ser iguais no servidor
    secret_key = os.getenv('SECRET_KEY', 'sua-chave-secreta-muito-longa-e-complexa-aqui')
    license_key = "TEST-KEY-123"
    app_name = "OperadorConquistador"
    device_id = f"test-device-{uuid.uuid4().hex[:8]}"
    
    # Calcula hash válido
    security_hash = calcular_hash(license_key, device_id, app_name, secret_key)
    
    # Dados para teste
    test_data = {
        'license_key': license_key,
        'device_id': device_id,
        'app_name': app_name,
        'hash': security_hash
    }
    
    endpoints = [
        ('/api/time', 'GET', None),
        ('/api/quantum/validate', 'POST', test_data),
        ('/api/quantum/activate', 'POST', test_data)
    ]
    
    for endpoint, method, data in endpoints:
        try:
            start = datetime.now()
            
            if method == 'GET':
                response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
            else:
                response = requests.post(
                    f'http://localhost:5000{endpoint}',
                    json=data,
                    timeout=5
                )
                
            latency = (datetime.now() - start).total_seconds() * 1000  # ms
            
            print(f"{endpoint} [{method}] - Status: {response.status_code} - Tempo: {latency:.2f}ms")
            
            if response.status_code >= 400:
                print(f"   ERRO: {response.text}")
                
        except Exception as e:
            print(f"{endpoint} [{method}] - FALHA: {str(e)}")

if __name__ == '__main__':
    testar_conexao_servidor()