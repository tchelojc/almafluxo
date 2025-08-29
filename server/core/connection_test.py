import requests
import socket
import logging
from urllib3.exceptions import InsecureRequestWarning

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Desativa avisos de SSL (apenas para testes)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def check_port_open(host, port, timeout=2):
    """Verifica se a porta está aberta localmente"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def test_local_connection(base_url):
    """Testa a conexão básica local"""
    try:
        logger.info(f"Testando conexão local: {base_url}")
        
        # Primeiro verifica se a porta está aberta
        parsed_url = requests.utils.urlparse(base_url)
        if not check_port_open(parsed_url.hostname, parsed_url.port):
            logger.error("Porta não está respondendo")
            return False
            
        response = requests.get(base_url, timeout=5, verify=False)
        logger.info(f"Resposta local: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erro na conexão local: {str(e)}")
        return False

def test_server_status(base_url):
    """Testa o endpoint /admin/server_status"""
    try:
        url = f"{base_url}/admin/server_status"
        logger.info(f"Testando endpoint server_status: {url}")
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Fluxon-Admin-Test'
        }
        
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        logger.info(f"Resposta do server_status: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'online'
        return False
    except Exception as e:
        logger.error(f"Erro no teste de server_status: {str(e)}")
        return False

def test_admin_token(base_url, admin_token):
    """Testa a validação do token de admin"""
    try:
        url = f"{base_url}/admin/verify_token"
        logger.info(f"Testando token admin em: {url}")
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        logger.info(f"Resposta do verify_token: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('valid', False)
        return False
    except Exception as e:
        logger.error(f"Erro no teste de token admin: {str(e)}")
        return False

def run_local_tests():
    LOCAL_URL = "http://localhost:5000"
    ADMIN_TOKEN = "seu_token_admin_aqui"  # Substitua pelo token real
    
    print("\n=== Iniciando Testes Locais ===\n")
    
    # Teste 1: Conexão básica
    print("1. Testando conexão básica...")
    if not test_local_connection(LOCAL_URL):
        print("❌ Servidor local não está respondendo")
        return
    print("✅ Conexão básica OK")
    
    # Teste 2: Status do servidor
    print("\n2. Testando status do servidor...")
    if not test_server_status(LOCAL_URL):
        print("❌ Status do servidor inválido")
        return
    print("✅ Status do servidor OK")
    
    # Teste 3: Token de administração
    print("\n3. Testando token de administração...")
    if not test_admin_token(LOCAL_URL, ADMIN_TOKEN):
        print("❌ Falha na validação do token admin")
        return
    print("✅ Token de administração OK")
    
    print("\n=== Todos os testes locais passaram com sucesso! ===")

if __name__ == '__main__':
    run_local_tests()