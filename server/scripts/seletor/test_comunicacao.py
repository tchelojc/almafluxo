# test_comunicacao.py
import requests
import json

def test_comunicacao():
    # Teste de login
    login_url = "http://localhost:5000/login"
    login_data = {
        "email": "admin@fluxon.com",
        "password": "nova_senha_admin_123"
    }
    
    try:
        # Teste de login
        response = requests.post(login_url, json=login_data, timeout=10)
        print(f"Status do login: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json()['data']['token']
            print("✅ Login bem-sucedido!")
            
            # Teste de verificação de token
            check_url = "http://localhost:5000/api/check_session"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            check_response = requests.get(check_url, headers=headers, timeout=10)
            print(f"Status da verificação: {check_response.status_code}")
            
            if check_response.status_code == 200:
                print("✅ Token verificado com sucesso!")
                return True
            else:
                print("❌ Falha na verificação do token")
                return False
        else:
            print("❌ Falha no login")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão: {str(e)}")
        return False

if __name__ == "__main__":
    test_comunicacao()