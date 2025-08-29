import requests
import pytest

def test_server_connection():
    """Testa a conexão básica com o servidor"""
    try:
        response = requests.get("http://127.0.0.1:5000/healthcheck", timeout=5)
        assert response.status_code == 200
        assert response.json().get("status") == "ok"
    except requests.exceptions.ConnectionError:
        pytest.fail("Servidor não está respondendo")

def test_license_validation():
    """Testa a validação de licença"""
    test_data = {
        "license_key": "TEST-KEY-123",
        "device_id": "TEST-DEVICE-001"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/validate",
            json=test_data,
            timeout=5
        )
        assert response.status_code in [200, 404]  # 404 se a licença não existir
    except requests.exceptions.ConnectionError:
        pytest.fail("Falha na conexão com o servidor")