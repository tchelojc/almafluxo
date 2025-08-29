import requests
import json
import subprocess
import time

def verificar_servico(porta, nome):
    try:
        response = requests.get(f"http://localhost:{porta}/health", timeout=5)
        print(f"✅ {nome} (porta {porta}): ONLINE - {response.status_code}")
        return True
    except:
        print(f"❌ {nome} (porta {porta}): OFFLINE")
        return False

def verificar_processo_ngrok():
    try:
        # Verifica se o ngrok está rodando
        result = subprocess.run(['tasklist', '/fi', 'imagename eq ngrok.exe'], 
                              capture_output=True, text=True)
        if 'ngrok.exe' in result.stdout:
            print("✅ Processo Ngrok: EXECUTANDO")
            return True
        else:
            print("❌ Processo Ngrok: NÃO ENCONTRADO")
            return False
    except:
        print("❌ Não foi possível verificar processo Ngrok")
        return False

def testar_autenticacao():
    try:
        response = requests.post(
            "http://localhost:5000/login",
            json={"email": "admin@fluxon.com", "password": "nova_senha_admin_123"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Autenticação: SUCESSO")
            token = response.json().get('data', {}).get('token')
            return token
        else:
            print(f"❌ Autenticação: FALHA - {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Autenticação: ERRO - {str(e)}")
        return None

def main():
    print("=== DIAGNÓSTICO DO SISTEMA FLUXON ===\n")
    
    # Verificar serviços
    verificar_servico(5000, "Servidor Flask")
    verificar_processo_ngrok()
    
    # Testar autenticação
    token = testar_autenticacao()
    
    if token:
        # Testar acesso à API com token
        try:
            response = requests.get(
                "http://localhost:5000/api/check_session",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            if response.status_code == 200:
                print("✅ API com token: ACESSO PERMITIDO")
            else:
                print(f"❌ API com token: ACESSO NEGADO - {response.status_code}")
        except Exception as e:
            print(f"❌ API com token: ERRO - {str(e)}")
    
    print("\n=== FIM DO DIAGNÓSTICO ===")

if __name__ == "__main__":
    main()