# test_server.py
import requests

def test_server():
    try:
        # Teste de health check
        health = requests.get('http://localhost:5000/health', timeout=5)
        print(f"Health check: {health.status_code} - {health.text}")
        
        # Teste de login
        login = requests.post(
            'http://localhost:5000/login',
            json={"email": "tchelojc@gmail.com", "password": "KGZO7OIDP8NL8JAJ"},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"Login: {login.status_code} - {login.text}")
        
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    test_server()